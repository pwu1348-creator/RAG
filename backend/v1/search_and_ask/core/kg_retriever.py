"""
知识图谱检索器 — 基于图的多跳推理检索

流程：
  1. 从查询中提取关键实体
  2. 在 KG 中搜索相关实体
  3. 执行多跳推理扩展关联实体
  4. 根据扩展的实体检索相关文档块
  5. 与向量/关键词检索结果融合
"""

import asyncio
from typing import List, Dict, Any, Set

from config import config
from services.knowledge_graph_service import KnowledgeGraphService
from services.embedding_service import EmbeddingService
from services.chromadb_service import ChromaDBService
from utils.logger import logger


class KGRetriever:
    """知识图谱检索器"""
    
    def __init__(self):
        self.kg_service = KnowledgeGraphService()
        self.embedding_service = EmbeddingService()
        self.chromadb_service = ChromaDBService()
    
    def search(
        self,
        query: str,
        knowledge_base_id: str,
        top_k: int = 10,
        use_hops: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        基于知识图谱的检索
        
        Args:
            query: 用户查询
            knowledge_base_id: 知识库ID
            top_k: 返回结果数量
            use_hops: 是否使用多跳推理
        
        Returns:
            检索结果列表
        """
        if not self.kg_service.is_enabled():
            logger.warning("[KGRetriever] 知识图谱已禁用")
            return []
        
        try:
            # Step 1: 从查询中提取实体
            query_entities = self._extract_entities_from_query(query)
            if not query_entities:
                logger.debug("[KGRetriever] 查询中未识别到实体，跳过 KG 检索")
                return []
            
            logger.info(f"[KGRetriever] 识别的查询实体: {query_entities}")
            
            # Step 2: 搜索相关实体（包含多跳）
            related_entities = self._find_related_entities(
                query_entities,
                use_hops=use_hops,
                hops=config.kg.HOP_LIMIT
            )
            
            if not related_entities:
                logger.debug("[KGRetriever] 未找到相关实体")
                return []
            
            logger.info(f"[KGRetriever] 扩展的相关实体: {related_entities}")
            
            # Step 3: 根据实体检索相关文档块
            results = self._retrieve_chunks_by_entities(
                related_entities,
                knowledge_base_id,
                top_k
            )
            
            return results
        
        except Exception as e:
            logger.error(f"[KGRetriever] 检索失败: {e}", exc_info=True)
            return []
    
    def _extract_entities_from_query(self, query: str) -> List[str]:
        """
        从查询中提取实体名称
        
        简单实现：将查询按空格分词，保留较长的词
        更复杂的方式可以调用 NER 模型或 LLM
        """
        # 移除常见的停用词
        stopwords = {
            "的", "是", "在", "和", "有", "这", "那", "了", "吗", "呢",
            "你", "我", "他", "她", "它", "们", "怎样", "什么", "如何"
        }
        
        # 简单分词（中文）
        words = []
        current_word = ""
        for char in query:
            if ord(char) >= 0x4E00 and ord(char) <= 0x9FFF:  # 中文字符
                current_word += char
            else:
                if current_word and current_word not in stopwords:
                    words.append(current_word)
                current_word = ""
        
        if current_word and current_word not in stopwords:
            words.append(current_word)
        
        # 保留长度 >= 2 的词
        entities = [w for w in words if len(w) >= 2]
        return entities[:5]  # 最多 5 个实体
    
    def _find_related_entities(
        self,
        query_entities: List[str],
        use_hops: bool = True,
        hops: int = 2
    ) -> Set[str]:
        """
        从查询实体出发，查找相关实体
        """
        related = set(query_entities)
        
        if not use_hops:
            return related
        
        # 多跳扩展
        for entity_name in query_entities:
            try:
                kg_result = self.kg_service.multi_hop_search(
                    entity_name=entity_name,
                    hops=hops,
                    limit=20
                )
                
                for entity in kg_result.get("entities", []):
                    related.add(entity.get("name", ""))
            
            except Exception as e:
                logger.warning(f"[KGRetriever] 多跳搜索失败 ({entity_name}): {e}")
        
        return related
    
    def _retrieve_chunks_by_entities(
        self,
        entities: Set[str],
        knowledge_base_id: str,
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """
        根据实体集合检索相关文档块
        
        策略：
          1. 对每个实体进行向量搜索（作为伪查询）
          2. 聚合结果并按相关性排序
        """
        results_by_chunk = {}  # chunk_id -> result
        
        try:
            for entity in list(entities)[:10]:  # 限制实体数量
                try:
                    # 对实体进行向量编码
                    embeddings = self.embedding_service.encode([entity])
                    if not embeddings or len(embeddings) == 0:
                        continue
                    
                    entity_embedding = embeddings[0]
                    
                    # 向量搜索
                    raw_results = self.chromadb_service.collection.query(
                        query_embeddings=[entity_embedding],
                        n_results=top_k * 2,
                        where={"kb_id": knowledge_base_id},
                        include=["documents", "metadatas", "distances"],
                    )
                    
                    # 处理结果
                    ids = raw_results.get("ids", [[]])[0]
                    docs = raw_results.get("documents", [[]])[0]
                    metas = raw_results.get("metadatas", [[]])[0]
                    dists = raw_results.get("distances", [[]])[0]
                    
                    for i in range(len(ids)):
                        chunk_id = ids[i]
                        if chunk_id not in results_by_chunk:
                            meta = metas[i] if i < len(metas) else {}
                            results_by_chunk[chunk_id] = {
                                "chunk_id": chunk_id,
                                "content": docs[i] if i < len(docs) else "",
                                "doc_id": meta.get("doc_id", ""),
                                "kb_id": knowledge_base_id,
                                "chunk_index": meta.get("chunk_index", 0),
                                "page_idx": meta.get("page_idx", 0),
                                "type": meta.get("chunk_type", meta.get("type", "text")),
                                "kg_scores": [],
                                "metadata": meta,
                            }
                        
                        # 累积相似度分数
                        similarity = 1.0 - float(dists[i]) if i < len(dists) else 0.0
                        results_by_chunk[chunk_id]["kg_scores"].append(similarity)
                
                except Exception as e:
                    logger.warning(f"[KGRetriever] 实体检索失败 ({entity}): {e}")
            
            # 计算聚合分数
            final_results = []
            for chunk_id, result in results_by_chunk.items():
                scores = result.pop("kg_scores")
                if scores:
                    result["kg_similarity"] = sum(scores) / len(scores)
                    final_results.append(result)
            
            # 按 KG 相似度排序
            final_results.sort(
                key=lambda x: x.get("kg_similarity", 0),
                reverse=True
            )
            
            return final_results[:top_k]
        
        except Exception as e:
            logger.error(f"[KGRetriever] 块检索失败: {e}")
            return []


class KGHybridRetriever:
    """知识图谱 + 混合检索融合器"""
    
    def __init__(self):
        self.kg_retriever = KGRetriever()
    
    def fuse_results(
        self,
        hybrid_results: List[Dict[str, Any]],
        kg_results: List[Dict[str, Any]],
        kg_weight: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        融合混合检索和知识图谱检索结果
        
        Args:
            hybrid_results: 混合检索结果（含 rrf_score 或 rerank_score）
            kg_results: 知识图谱检索结果（含 kg_similarity）
            kg_weight: 知识图谱结果的权重
        
        Returns:
            融合后的结果列表
        """
        if not kg_results:
            return hybrid_results
        
        # 构建 chunk_id -> result 的映射
        results_map: Dict[str, Dict[str, Any]] = {}
        
        # 添加混合检索结果
        for i, result in enumerate(hybrid_results):
            chunk_id = result.get("chunk_id")
            if chunk_id:
                result["hybrid_score"] = result.get(
                    "rerank_score", result.get("rrf_score", 0)
                )
                result["hybrid_rank"] = i
                results_map[chunk_id] = result
        
        # 融合知识图谱结果
        for i, result in enumerate(kg_results):
            chunk_id = result.get("chunk_id")
            if chunk_id:
                kg_similarity = result.get("kg_similarity", 0)
                
                if chunk_id in results_map:
                    # 已有混合检索结果，加权融合
                    existing = results_map[chunk_id]
                    hybrid_score = existing.get("hybrid_score", 0)
                    fused_score = (
                        (1 - kg_weight) * hybrid_score +
                        kg_weight * kg_similarity
                    )
                    existing["fused_score"] = fused_score
                    existing["kg_enhanced"] = True
                else:
                    # 仅 KG 检索到
                    result["fused_score"] = kg_weight * kg_similarity
                    result["kg_enhanced"] = False
                    results_map[chunk_id] = result
        
        # 按融合分数排序
        fused = list(results_map.values())
        fused.sort(
            key=lambda x: x.get("fused_score", x.get("hybrid_score", 0)),
            reverse=True
        )
        
        return fused
