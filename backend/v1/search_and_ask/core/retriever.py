
import json
import math
from typing import List, Dict, Any, Optional
from collections import defaultdict
from dataclasses import dataclass

import pymysql
from pymysql.cursors import DictCursor

from config import config
from utils.rag_tokenizer import RagTokenizer
from services.chromadb_service import ChromaDBService
from services.embedding_service import EmbeddingService
from utils.logger import logger


def _resolve_tenant_id(knowledge_base_id: str) -> str:
    try:
        conn = pymysql.connect(
            host=config.mysql.HOST,
            port=config.mysql.PORT,
            user=config.mysql.USER,
            password=config.mysql.PASSWORD,
            database=config.mysql.DATABASE,
            charset="utf8mb4",
            cursorclass=DictCursor,
        )
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT owner_id FROM knowledge_bases WHERE kb_id = %s LIMIT 1",
                    (knowledge_base_id,),
                )
                row = cursor.fetchone()
                if row and row.get("owner_id"):
                    return row["owner_id"]
    except Exception as e:
        logger.warning(f"[Retriever] 查询 tenant_id 失败: {e}")
    return ""


class BM25Retriever:

    def __init__(self):
        self.tokenizer = RagTokenizer()
        self.documents: List[Dict[str, Any]] = []
        self.doc_freq = defaultdict(int)
        self.avg_doc_len = 0.0
        self.n_docs = 0
        self.bm25_params = {"k1": 1.5, "b": 0.75}

    def reset(self):
        self.documents.clear()
        self.doc_freq.clear()
        self.avg_doc_len = 0.0
        self.n_docs = 0

    def add_documents(self, docs: List[Dict[str, Any]]):
        self.documents = docs
        self.n_docs = len(docs)
        if self.n_docs == 0:
            return

        total_len = 0
        for doc in docs:
            tokens = self._tokenize(doc.get("content", ""))
            total_len += len(tokens)
            for token in set(tokens):
                self.doc_freq[token] += 1
        self.avg_doc_len = total_len / self.n_docs

    def search(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        query_tokens = self._tokenize(query)
        if not query_tokens or not self.documents:
            return []

        scored = []
        for i, doc in enumerate(self.documents):
            score = self._bm25_score(query_tokens, self._tokenize(doc.get("content", "")))
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


@dataclass
class RerankResult:
    index: int
    score: float


class Reranker:

    def __init__(self):
        self.base_url = config.reranker.BASE_URL
        self.api_key = config.reranker.API_KEY
        self.model = config.reranker.MODEL

    def rerank(self, query: str, candidates: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        import requests

        sentences = [doc.get("content", "")[:512] for doc in candidates]
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Failover-Enabled": "true",
        }
        payload = {
            "model": self.model,
            "inputs": {"source_sentence": query, "sentences": sentences},
        }

        try:
            resp = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            scores = resp.json()

            if isinstance(scores, list) and len(scores) == len(candidates):
                for i, doc in enumerate(candidates):
                    doc["rerank_score"] = float(scores[i])
            else:
                logger.warning(f"[Reranker] API 返回格式异常，跳过重排")
                return candidates[:top_k]

            candidates.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
            return candidates[:top_k]

        except Exception as e:
            logger.warning(f"[Reranker] API 调用失败，跳过重排: {e}")
            return candidates[:top_k]


class HybridRetriever:

    DEFAULT_FIELDS = [
        "docnm_kwd", "content_ltks", "kb_id", "img_id",
        "title_tks", "position_int", "doc_id", "page_num_int",
        "top_int", "create_timestamp_flt",
    ]

    def __init__(self):
        self._bm25_map: Dict[str, BM25Retriever] = {}
        self.chromadb = ChromaDBService()
        self.embedding = EmbeddingService()
        self._initialized_kbs: set = set()
        self._tenant_id: str = ""

    def initialize(self, knowledge_base_id: str, tenant_id: str = ""):
        if tenant_id:
            self._tenant_id = tenant_id
        if knowledge_base_id in self._initialized_kbs:
            return

        try:
            collection = self.chromadb.get_collection(self._tenant_id) if self._tenant_id else None
            if not collection:
                logger.warning(f"[HybridRetriever] 无法获取 collection, tenant_id={self._tenant_id}")
                return

            results = collection.get(
                where={"kb_id": knowledge_base_id},
                include=["documents", "metadatas"],
            )

            child_docs = []
            ids = results.get("ids", [])
            documents = results.get("documents", [])
            metadatas = results.get("metadatas", [])

            for i in range(len(ids)):
                meta = metadatas[i] if i < len(metadatas) else {}
                child_docs.append({
                    "chunk_id": ids[i],
                    "content": documents[i] if i < len(documents) else "",
                    "content_ltks": meta.get("content_ltks", ""),
                    "content_sm_ltks": meta.get("content_sm_ltks", ""),
                    "title_tks": meta.get("title_tks", ""),
                    "title_sm_tks": meta.get("title_sm_tks", ""),
                    "doc_id": meta.get("doc_id", ""),
                    "kb_id": meta.get("kb_id", knowledge_base_id),
                    "docnm_kwd": meta.get("docnm_kwd", ""),
                    "page_num_int": json.loads(meta.get("page_num_int", "[]")),
                    "position_int": json.loads(meta.get("position_int", "[]")),
                    "top_int": json.loads(meta.get("top_int", "[1]")),
                    "create_time": meta.get("create_time", ""),
                    "create_timestamp_flt": meta.get("create_timestamp_flt", 0.0),
                    "img_id": meta.get("img_id", ""),
                    "metadata": meta,
                })

            bm25 = BM25Retriever()
            bm25.add_documents(child_docs)
            self._bm25_map[knowledge_base_id] = bm25
            self._initialized_kbs.add(knowledge_base_id)
            logger.info(f"[HybridRetriever] KB={knowledge_base_id} 初始化完成，块数={len(child_docs)}")
        except Exception as e:
            logger.error(f"[HybridRetriever] 初始化失败 KB={knowledge_base_id}: {e}")
            raise

    def reset(self):
        self._initialized_kbs.clear()
        self._bm25_map.clear()

    def get_filters(self, kb_ids: List[str] = None, doc_ids: List[str] = None) -> Optional[Dict]:
        conditions = []
        if kb_ids:
            conditions.append({"kb_id": kb_ids[0]} if len(kb_ids) == 1 else {"kb_id": {"$in": kb_ids}})
        if doc_ids:
            conditions.append({"doc_id": doc_ids[0]} if len(doc_ids) == 1 else {"doc_id": {"$in": doc_ids}})
        if not conditions:
            return None
        return conditions[0] if len(conditions) == 1 else {"$and": conditions}

    def search(
        self,
        query: str,
        knowledge_base_id: str,
        tenant_id: str = "",
        top_k: int = 20,
        doc_ids: List[str] = None,
        bm25_weight: float = 1.0,
        vector_weight: float = 1.0,
    ) -> List[Dict[str, Any]]:
        if tenant_id:
            self._tenant_id = tenant_id
        self.initialize(knowledge_base_id, tenant_id)

        bm25 = self._bm25_map.get(knowledge_base_id, BM25Retriever())
        bm25_results = bm25.search(query, top_k)

        vector_results = []
        try:
            query_emb = self.embedding.encode([query])[0]
            collection = self.chromadb.get_collection(self._tenant_id)
            filters = self.get_filters(kb_ids=[knowledge_base_id], doc_ids=doc_ids)

            raw = collection.query(
                query_embeddings=[query_emb],
                n_results=top_k,
                where=filters,
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
                    "content_ltks": meta.get("content_ltks", ""),
                    "title_tks": meta.get("title_tks", ""),
                    "doc_id": meta.get("doc_id", ""),
                    "kb_id": meta.get("kb_id", knowledge_base_id),
                    "docnm_kwd": meta.get("docnm_kwd", ""),
                    "page_num_int": json.loads(meta.get("page_num_int", "[]")),
                    "position_int": json.loads(meta.get("position_int", "[]")),
                    "top_int": json.loads(meta.get("top_int", "[1]")),
                    "create_timestamp_flt": meta.get("create_timestamp_flt", 0.0),
                    "img_id": meta.get("img_id", ""),
                    "similarity": 1.0 - float(dists0[i]) if i < len(dists0) else 0.0,
                    "metadata": meta,
                })
        except Exception as e:
            logger.error(f"[HybridRetriever] 向量检索失败: {e}")

        return self._rrf_fuse(
            bm25_results, vector_results,
            w_a=bm25_weight, w_b=vector_weight,
        )[:top_k]

    def token_rerank(self, query: str, candidates: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        tokenizer = RagTokenizer()
        query_tks = set(tokenizer.tokenize(query).split())

        for c in candidates:
            content_tks = c.get("content_ltks", "").split()
            title_tks = [t for t in c.get("title_tks", "").split() if t]
            weighted_tks = content_tks + title_tks * 2
            if not weighted_tks:
                c["token_rerank_score"] = 0.0
                continue
            overlap = sum(1 for t in weighted_tks if t in query_tks)
            c["token_rerank_score"] = overlap / max(len(query_tks), 1)

        candidates.sort(key=lambda x: x.get("token_rerank_score", 0), reverse=True)
        return candidates[:top_k]

    @staticmethod
    def _rrf_fuse(
        list_a: List[Dict],
        list_b: List[Dict],
        w_a: float = 1.0,
        w_b: float = 1.0,
        k: int = 60,
    ) -> List[Dict[str, Any]]:
        scores: Dict[str, float] = defaultdict(float)
        doc_map: Dict[str, Dict] = {}

        for i, doc in enumerate(list_a):
            key = doc.get("chunk_id", str(i))
            scores[key] += w_a * 1.0 / (k + i + 1)
            doc_map[key] = doc

        for i, doc in enumerate(list_b):
            key = doc.get("chunk_id", str(i))
            scores[key] += w_b * 1.0 / (k + i + 1)
            if key not in doc_map:
                doc_map[key] = doc

        sorted_keys = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        results = []
        for key, rrf in sorted_keys:
            d = dict(doc_map.get(key, {}))
            d["rrf_score"] = rrf
            results.append(d)
        return results


class SearchService:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_hybrid"):
            return
        self._hybrid = HybridRetriever()
        self._reranker = Reranker()

    def search(
        self,
        query: str,
        knowledge_base_id: str,
        tenant_id: str = "",
        top_k: int = 10,
        min_score: float = 0.3,
        use_hybrid: bool = True,
        use_rerank: bool = True,
        use_kg: bool = True,
        kg_weight: float = 0.3,
        doc_ids: List[str] = None,
        bm25_weight: float = 1.0,
        vector_weight: float = 1.0,
    ) -> List[Dict[str, Any]]:
        if not tenant_id:
            tenant_id = _resolve_tenant_id(knowledge_base_id)
            if not tenant_id:
                logger.error(f"[SearchService] 无法解析 tenant_id, kb_id={knowledge_base_id}")
                return []

        if not use_hybrid:
            self._hybrid.initialize(knowledge_base_id, tenant_id)
            bm25 = self._hybrid._bm25_map.get(knowledge_base_id, BM25Retriever())
            return bm25.search(query, top_k)

        candidates = self._hybrid.search(
            query=query,
            knowledge_base_id=knowledge_base_id,
            tenant_id=tenant_id,
            top_k=top_k * 3,
            doc_ids=doc_ids,
            bm25_weight=bm25_weight,
            vector_weight=vector_weight,
        )

        if not candidates:
            return []

        if use_rerank:
            try:
                candidates = self._reranker.rerank(query, candidates, top_k=top_k)
            except Exception as e:
                logger.warning(f"[SearchService] Rerank 失败: {e}")
                candidates = candidates[:top_k]
        else:
            candidates = candidates[:top_k]

        if min_score > 0:
            before = len(candidates)
            candidates = [
                r for r in candidates
                if r.get("rerank_score", r.get("rrf_score", r.get("similarity", 0))) >= min_score
            ]
            if before > 0 and not candidates:
                logger.warning(f"[SearchService] min_score={min_score} 过滤后为空，考虑降低阈值")

        if use_kg and candidates:
            try:
                from core.kg_retriever import KGRetriever, KGHybridRetriever
                kg_results = KGRetriever().search(query=query, knowledge_base_id=knowledge_base_id, top_k=top_k, use_hops=True)
                if kg_results:
                    candidates = KGHybridRetriever().fuse_results(candidates, kg_results, kg_weight=kg_weight)
            except Exception as e:
                logger.warning(f"[SearchService] KG 融合失败: {e}")

        logger.info(f"[SearchService] query='{query[:30]}' kb={knowledge_base_id} results={len(candidates)}")
        return candidates

    def reset(self):
        self._hybrid.reset()
