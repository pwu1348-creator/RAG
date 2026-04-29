"""
核心模块：检索器

完整检索流水线：
  query → 子块混合检索 (BM25 + 向量 + RRF) → BGE Reranker 重排
       → 根据 parent_chunk_id 取回父块 → 去重 → 返回父块上下文

组件：
  BM25Retriever         — 自实现 BM25 关键词检索（仅索引子块）
  Reranker              — BGE-reranker-base 重排序器
  HybridRetriever       — BM25 + 向量检索 + RRF 融合
  ParentChildRetriever  — 父子检索编排器（完整流水线）
  SearchService         — 对外统一检索接口（单例）
"""

import os
import math
from typing import List, Dict, Any, Optional
from collections import defaultdict
from dataclasses import dataclass

from config import config
from utils.rag_tokenizer import RagTokenizer
from services.chromadb_service import ChromaDBService
from services.embedding_service import EmbeddingService
from utils.logger import logger


# ============================================================================
# BM25 检索器（子块限定）
# ============================================================================

class BM25Retriever:
    """
    BM25 全文检索器。

    仅索引 chunk_type='child' 的子块，每个子块持有 parent_chunk_id，
    检索结果中保留该字段，供上层回退父块。
    """

    def __init__(self):
        self.tokenizer = RagTokenizer()
        self.documents: List[Dict[str, Any]] = []
        self.doc_freq = defaultdict(int)
        self.avg_doc_len = 0.0
        self.n_docs = 0
        self.bm25_params = {"k1": 1.5, "b": 0.75}

    def reset(self):
        """清空索引"""
        self.documents.clear()
        self.doc_freq.clear()
        self.avg_doc_len = 0.0
        self.n_docs = 0

    def add_documents(self, docs: List[Dict[str, Any]]):
        """批量添加子块到 BM25 索引"""
        self.documents = docs
        self.n_docs = len(docs)
        if self.n_docs == 0:
            return

        total_len = 0
        for doc in docs:
            content = doc.get("content", "")
            tokens = self._tokenize(content)
            total_len += len(tokens)
            for token in set(tokens):
                self.doc_freq[token] += 1

        self.avg_doc_len = total_len / self.n_docs

    def search(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """BM25 关键词检索"""
        query_tokens = self._tokenize(query)
        if not query_tokens or not self.documents:
            return []

        scored = []
        for i, doc in enumerate(self.documents):
            content = doc.get("content", "")
            score = self._bm25_score(query_tokens, self._tokenize(content))
            if score > 0:
                scored.append((i, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [
            {**dict(self.documents[idx]), "bm25_score": score}
            for idx, score in scored[:top_k]
        ]

    def _tokenize(self, text: str) -> List[str]:
        if not text:
            return []
        return self.tokenizer.tokenize(text).split()

    def _bm25_score(self, query_tokens: List[str], doc_tokens: List[str]) -> float:
        score = 0.0
        doc_len = len(doc_tokens)
        freq = defaultdict(int)
        for t in doc_tokens:
            freq[t] += 1

        k1, b = self.bm25_params["k1"], self.bm25_params["b"]
        for token in query_tokens:
            if token not in freq:
                continue
            f = freq[token]
            df = self.doc_freq.get(token, 0)
            idf = math.log((self.n_docs - df + 0.5) / (df + 0.5) + 1)
            tf = (f * (k1 + 1)) / (f + k1 * (1 - b + b * doc_len / max(self.avg_doc_len, 1)))
            score += idf * tf
        return score


# ============================================================================
# BGE Reranker
# ============================================================================

@dataclass
class RerankResult:
    index: int
    score: float


class Reranker:
    """
    BGE Reranker 封装。

    使用 bge-reranker-base 对候选子块做精确相关性重排序。
    延迟加载：首次调用时下载/加载模型，启动时不阻塞。
    """

    def __init__(self, model_name: str = "BAAI/bge-reranker-base", use_fp16: bool = True):
        self.model_name = model_name
        self.use_fp16 = use_fp16
        self._reranker = None

    def _lazy_init(self):
        if self._reranker is not None:
            return
        try:
            from FlagEmbedding import FlagReranker
            self._reranker = FlagReranker(self.model_name, use_fp16=self.use_fp16)
            logger.info(f"[Reranker] 模型已加载: {self.model_name}")
        except ImportError:
            logger.error("[Reranker] FlagEmbedding 未安装，请执行: pip install FlagEmbedding")
            raise
        except Exception as e:
            logger.error(f"[Reranker] 模型加载失败: {e}")
            raise

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """对候选子块重排序，返回 top_k 条"""
        if not candidates:
            return []

        self._lazy_init()

        pairs = [[query, doc.get("content", "")] for doc in candidates]
        try:
            scores = self._reranker.compute_score(pairs, normalize=True)
        except Exception:
            scores = [self._reranker.compute_score([p], normalize=True)[0] for p in pairs]

        if not isinstance(scores, list):
            scores = [scores]

        for i, doc in enumerate(candidates):
            doc["rerank_score"] = float(scores[i]) if i < len(scores) else 0.0

        candidates.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
        return candidates[:top_k]


# ============================================================================
# 混合检索器
# ============================================================================

class HybridRetriever:
    """
    混合检索器：BM25 + 向量检索 + RRF 融合。

    仅在子块层面做检索，不涉及父块。
    每个知识库维护独立的 BM25 索引，避免多 KB 场景下互相覆盖。
    """

    def __init__(self):
        # 每个 kb_id 对应一个独立的 BM25Retriever
        self._bm25_map: Dict[str, BM25Retriever] = {}
        self.chromadb = ChromaDBService()
        self.embedding = EmbeddingService()
        self._initialized_kbs: set = set()

    # 向后兼容：外部代码可能直接访问 self.bm25
    @property
    def bm25(self) -> BM25Retriever:
        """返回最近一次使用的 BM25 实例（向后兼容）"""
        if not self._bm25_map:
            return BM25Retriever()
        return next(iter(self._bm25_map.values()))

    def initialize(self, knowledge_base_id: str):
        """从 ChromaDB 加载子块到对应 KB 的 BM25 索引"""
        if knowledge_base_id in self._initialized_kbs:
            return

        try:
            results = self.chromadb.collection.get(
                where={"kb_id": knowledge_base_id},
                include=["documents", "metadatas"],
            )

            child_docs = []
            ids = results.get("ids", [])
            documents = results.get("documents", [])
            metadatas = results.get("metadatas", [])

            for i in range(len(ids)):
                meta = metadatas[i] if i < len(metadatas) else {}
                chunk_type = meta.get("chunk_type", meta.get("type", "text"))
                if chunk_type not in ("child", "child_text"):
                    continue

                child_docs.append({
                    "chunk_id": ids[i],
                    "content": documents[i] if i < len(documents) else "",
                    "doc_id": meta.get("doc_id", ""),
                    "kb_id": meta.get("kb_id", knowledge_base_id),
                    "parent_chunk_id": meta.get("parent_chunk_id", ""),
                    "chunk_index": meta.get("chunk_index", 0),
                    "page_idx": meta.get("page_idx", 0),
                    "type": chunk_type,
                    "metadata": meta,
                })

            bm25 = BM25Retriever()
            bm25.add_documents(child_docs)
            self._bm25_map[knowledge_base_id] = bm25
            self._initialized_kbs.add(knowledge_base_id)
            logger.info(
                f"[HybridRetriever] KB={knowledge_base_id} 初始化完成，子块数={len(child_docs)}"
            )
        except Exception as e:
            logger.error(f"[HybridRetriever] 初始化失败 KB={knowledge_base_id}: {e}")
            raise

    def reset(self):
        """重置所有索引缓存"""
        self._initialized_kbs.clear()
        self._bm25_map.clear()

    def search(
        self,
        query: str,
        knowledge_base_id: str,
        top_k: int = 20,
    ) -> List[Dict[str, Any]]:
        """混合检索子块，返回 RRF 融合结果"""
        self.initialize(knowledge_base_id)

        # BM25（使用该 KB 专属索引）
        bm25 = self._bm25_map.get(knowledge_base_id, BM25Retriever())
        bm25_results = bm25.search(query, top_k)

        # 向量检索
        vector_results = []
        try:
            query_emb = self.embedding.encode([query])[0]
            raw = self.chromadb.collection.query(
                query_embeddings=[query_emb],
                n_results=top_k,
                where={"kb_id": knowledge_base_id},
                include=["documents", "metadatas", "distances"],
            )
            ids0 = raw.get("ids", [[]])[0]
            docs0 = raw.get("documents", [[]])[0]
            metas0 = raw.get("metadatas", [[]])[0]
            dists0 = raw.get("distances", [[]])[0]
            for i in range(len(ids0)):
                meta = metas0[i] if i < len(metas0) else {}
                vector_results.append({
                    "chunk_id": ids0[i],
                    "content": docs0[i] if i < len(docs0) else "",
                    "doc_id": meta.get("doc_id", ""),
                    "kb_id": meta.get("kb_id", knowledge_base_id),
                    "parent_chunk_id": meta.get("parent_chunk_id", ""),
                    "chunk_index": meta.get("chunk_index", 0),
                    "page_idx": meta.get("page_idx", 0),
                    "type": meta.get("chunk_type", meta.get("type", "text")),
                    "similarity": 1.0 - float(dists0[i]) if i < len(dists0) else 0.0,
                    "metadata": meta,
                })
        except Exception as e:
            logger.error(f"[HybridRetriever] 向量检索失败: {e}")

        # RRF 融合
        return self._rrf_fuse(bm25_results, vector_results)[:top_k]

    @staticmethod
    def _rrf_fuse(
        list_a: List[Dict[str, Any]],
        list_b: List[Dict[str, Any]],
        k: int = 60,
    ) -> List[Dict[str, Any]]:
        scores: Dict[str, float] = defaultdict(float)
        doc_map: Dict[str, Dict[str, Any]] = {}

        for i, doc in enumerate(list_a):
            key = doc.get("chunk_id", str(i))
            scores[key] += 1.0 / (k + i + 1)
            doc_map[key] = doc

        for i, doc in enumerate(list_b):
            key = doc.get("chunk_id", str(i))
            scores[key] += 1.0 / (k + i + 1)
            if key not in doc_map:
                doc_map[key] = doc

        sorted_keys = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        results = []
        for key, rrf in sorted_keys:
            d = dict(doc_map.get(key, {}))
            d["rrf_score"] = rrf
            results.append(d)
        return results


# ============================================================================
# 父子检索编排器
# ============================================================================

class ParentChildRetriever:
    """
    父子检索器（核心编排器）。

    流水线：
    1. HybridRetriever 在子块层做 BM25 + 向量 + RRF
    2. Reranker 对子块候选做 BGE 重排序
    3. 根据 parent_chunk_id 取回父块原文（去重）
    4. 合并父块及其子块得分元信息，返回最终结果
    """

    def __init__(self):
        self.hybrid = HybridRetriever()
        self.reranker = Reranker()
        self.chromadb = ChromaDBService()
        self._mysql = None

    def _get_mysql_conn(self):
        """获取独立的 MySQL 连接"""
        if self._mysql is None or not getattr(self._mysql, "open", False):
            import pymysql
            from pymysql.cursors import DictCursor
            self._mysql = pymysql.connect(
                host=config.mysql.HOST,
                port=config.mysql.PORT,
                user=config.mysql.USER,
                password=config.mysql.PASSWORD,
                database=config.mysql.DATABASE,
                charset="utf8mb4",
                cursorclass=DictCursor,
            )
        return self._mysql

    # ------------------------------------------------------------------
    # 主检索入口
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        knowledge_base_id: str,
        top_k: int = 10,
        candidate_size: int = 30,
        use_rerank: bool = True,
        fetch_parents: bool = True,
    ) -> Dict[str, Any]:
        """
        执行完整父子检索流水线。

        Returns:
            {"results": list, "total": int, "mode": "parent"|"child", "child_candidates": int}
        """
        # Step 1: 混合检索子块
        child_candidates = self.hybrid.search(
            query=query, knowledge_base_id=knowledge_base_id, top_k=candidate_size,
        )
        if not child_candidates:
            return {"results": [], "total": 0, "mode": "child", "child_candidates": 0}

        # Step 2: BGE 重排序
        if use_rerank:
            try:
                child_candidates = self.reranker.rerank(query, child_candidates, top_k=top_k * 2)
            except Exception as e:
                logger.warning(f"[ParentChildRetriever] Rerank 失败，使用 RRF 结果: {e}")

        # Step 3: 不回退父块时直接返回子块
        if not fetch_parents:
            return {
                "results": child_candidates[:top_k],
                "total": len(child_candidates[:top_k]),
                "mode": "child",
                "child_candidates": len(child_candidates),
            }

        # Step 4: 回退父块
        parent_results = self._fetch_parents(child_candidates, knowledge_base_id, top_k)
        return {
            "results": parent_results,
            "total": len(parent_results),
            "mode": "parent",
            "child_candidates": len(child_candidates),
        }

    # ------------------------------------------------------------------
    # 父块取回
    # ------------------------------------------------------------------

    def _fetch_parents(
        self,
        child_candidates: List[Dict[str, Any]],
        kb_id: str,
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """从候选子块提取唯一 parent_chunk_id，拉取父块原文，去重合并"""
        if not child_candidates:
            return []

        # 收集唯一 parent_chunk_id 并按子块得分排序
        parent_ids_seen = set()
        ordered_parent_ids = []
        child_scores_by_parent: Dict[str, List[float]] = defaultdict(list)

        for child in child_candidates:
            pid = child.get("parent_chunk_id", "") or child.get("chunk_id", "")
            if not pid:
                continue
            if pid not in parent_ids_seen:
                parent_ids_seen.add(pid)
                ordered_parent_ids.append(pid)
            score = child.get("rerank_score") or child.get("rrf_score") or child.get("similarity") or 0
            child_scores_by_parent[pid].append(score)

        ordered_parent_ids.sort(
            key=lambda pid: max(child_scores_by_parent[pid]), reverse=True
        )
        ordered_parent_ids = ordered_parent_ids[:top_k]

        # 加载父块内容
        parent_map = self._load_parent_contents(ordered_parent_ids, kb_id)

        # 组装结果
        results = []
        for pid in ordered_parent_ids:
            parent = parent_map.get(pid)
            if not parent:
                continue
            scores = child_scores_by_parent.get(pid, [])
            results.append({
                "chunk_id": pid,
                "content": parent.get("content", ""),
                "doc_id": parent.get("doc_id", ""),
                "kb_id": kb_id,
                "chunk_index": parent.get("chunk_index", 0),
                "page_idx": parent.get("page_idx", 0),
                "type": "parent",
                "score": max(scores) if scores else 0.0,
                "avg_score": sum(scores) / len(scores) if scores else 0.0,
                "child_count": len(scores),
            })

        return results

    def _load_parent_contents(
        self, parent_ids: List[str], kb_id: str
    ) -> Dict[str, Dict[str, Any]]:
        """从 ChromaDB / MySQL 加载父块内容"""
        parent_map: Dict[str, Dict[str, Any]] = {}

        # 尝试 ChromaDB
        try:
            existing = self.chromadb.collection.get(
                ids=parent_ids, include=["documents", "metadatas"],
            )
            for i in range(len(existing.get("ids", []))):
                pid = existing["ids"][i]
                meta = existing["metadatas"][i] if i < len(existing["metadatas"]) else {}
                parent_map[pid] = {
                    "chunk_id": pid,
                    "content": existing["documents"][i],
                    "doc_id": meta.get("doc_id", ""),
                    "chunk_index": meta.get("chunk_index", 0),
                    "page_idx": meta.get("page_idx", 0),
                }
        except Exception as e:
            logger.debug(f"[ParentChildRetriever] ChromaDB 父块查询失败: {e}")

        # 补齐 MySQL
        missing = [p for p in parent_ids if p not in parent_map]
        if missing:
            try:
                conn = self._get_mysql_conn()
                with conn.cursor() as cur:
                    ph = ",".join(["%s"] * len(missing))
                    cur.execute(
                        f"SELECT chunk_id, doc_id, content, chunk_index, page_idx "
                        f"FROM document_chunks WHERE chunk_id IN ({ph})",
                        missing,
                    )
                    for row in cur.fetchall():
                        pid = row["chunk_id"]
                        parent_map[pid] = {
                            "chunk_id": pid,
                            "content": row.get("content", ""),
                            "doc_id": row.get("doc_id", ""),
                            "chunk_index": row.get("chunk_index", 0),
                            "page_idx": row.get("page_idx", 0),
                        }
            except Exception as e:
                logger.error(f"[ParentChildRetriever] MySQL 父块查询失败: {e}")

        return parent_map


# ============================================================================
# 检索服务（对外 API）
# ============================================================================

class SearchService:
    """
    检索服务（单例）。

    封装 ParentChildRetriever，提供稳定的对外接口，保持与旧版兼容。
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_pc_retriever"):
            return
        self._pc_retriever = ParentChildRetriever()

    def search(
        self,
        query: str,
        knowledge_base_id: str,
        top_k: int = 10,
        min_score: float = 0.3,
        use_hybrid: bool = True,
        use_rerank: bool = True,
        fetch_parents: bool = True,
    ) -> List[Dict[str, Any]]:
        """检索接口：返回父块（或子块）列表"""
        # 纯 BM25 降级模式
        if not use_hybrid:
            hybrid = self._pc_retriever.hybrid
            hybrid.initialize(knowledge_base_id)
            bm25 = hybrid._bm25_map.get(knowledge_base_id, BM25Retriever())
            children = bm25.search(query, top_k * 3)
            if fetch_parents:
                return self._pc_retriever._fetch_parents(children, knowledge_base_id, top_k)
            return children[:top_k]

        # 完整流水线
        result = self._pc_retriever.search(
            query=query,
            knowledge_base_id=knowledge_base_id,
            top_k=top_k,
            candidate_size=top_k * 3,
            use_rerank=use_rerank,
            fetch_parents=fetch_parents,
        )

        results = result["results"]
        if min_score > 0:
            results = [r for r in results
                       if r.get("score", 0) >= min_score or r.get("avg_score", 0) >= min_score]

        return results

    def reset(self):
        """重置所有缓存（文档重索引后调用）"""
        self._pc_retriever.hybrid.reset()
