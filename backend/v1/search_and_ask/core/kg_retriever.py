
import asyncio
from typing import List, Dict, Any, Set

from config import config
from services.knowledge_graph_service import KnowledgeGraphService
from services.embedding_service import EmbeddingService
from services.chromadb_service import ChromaDBService
from core.retriever import _resolve_tenant_id
from utils.logger import logger


class KGRetriever:
    
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
        if not self.kg_service.is_enabled():
            logger.warning("[KGRetriever] 知识图谱已禁用")
            return []
        
        try:
            query_entities = self._extract_entities_from_query(query)
            if not query_entities:
                logger.debug("[KGRetriever] 查询中未识别到实体，跳过 KG 检索")
                return []
            
            logger.info(f"[KGRetriever] 识别的查询实体: {query_entities}")
            
            related_entities = self._find_related_entities(
                query_entities,
                use_hops=use_hops,
                hops=config.kg.HOP_LIMIT
            )
            
            if not related_entities:
                logger.debug("[KGRetriever] 未找到相关实体")
                return []
            
            logger.info(f"[KGRetriever] 扩展的相关实体: {related_entities}")
            
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
        stopwords = {
            "的", "是", "在", "和", "有", "这", "那", "了", "吗", "呢",
            "你", "我", "他", "她", "它", "们", "怎样", "什么", "如何"
        }
        
        words = []
        current_word = ""
        for char in query:
            if ord(char) >= 0x4E00 and ord(char) <= 0x9FFF:
                current_word += char
            else:
                if current_word and current_word not in stopwords:
                    words.append(current_word)
                current_word = ""
        
        if current_word and current_word not in stopwords:
            words.append(current_word)
        
        entities = [w for w in words if len(w) >= 2]
        return entities[:5]
    
    def _find_related_entities(
        self,
        query_entities: List[str],
        use_hops: bool = True,
        hops: int = 2
    ) -> Set[str]:
        related = set(query_entities)
        
        if not use_hops:
            return related
        
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
        results_by_chunk = {}
        
        try:
            # 通过 knowledge_base_id 解析 tenant_id 以获取正确的 collection
            tenant_id = _resolve_tenant_id(knowledge_base_id)
            if not tenant_id:
                logger.warning(f"[KGRetriever] 无法解析 tenant_id, kb_id={knowledge_base_id}")
                return []
            collection = self.chromadb_service.get_collection(tenant_id)
            if not collection:
                logger.warning(f"[KGRetriever] 无法获取 collection, tenant_id={tenant_id}")
                return []

            for entity in list(entities)[:10]:
                try:
                    embeddings = self.embedding_service.encode([entity])
                    if not embeddings or len(embeddings) == 0:
                        continue
                    
                    entity_embedding = embeddings[0]
                    
                    raw_results = collection.query(
                        query_embeddings=[entity_embedding],
                        n_results=top_k * 2,
                        where={"kb_id": knowledge_base_id},
                        include=["documents", "metadatas", "distances"],
                    )
                    
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
                        
                        similarity = 1.0 - float(dists[i]) if i < len(dists) else 0.0
                        results_by_chunk[chunk_id]["kg_scores"].append(similarity)
                
                except Exception as e:
                    logger.warning(f"[KGRetriever] 实体检索失败 ({entity}): {e}")
            
            final_results = []
            for chunk_id, result in results_by_chunk.items():
                scores = result.pop("kg_scores")
                if scores:
                    result["kg_similarity"] = sum(scores) / len(scores)
                    final_results.append(result)
            
            final_results.sort(
                key=lambda x: x.get("kg_similarity", 0),
                reverse=True
            )
            
            return final_results[:top_k]
        
        except Exception as e:
            logger.error(f"[KGRetriever] 块检索失败: {e}")
            return []


class KGHybridRetriever:
    
    def __init__(self):
        self.kg_retriever = KGRetriever()
    
    def fuse_results(
        self,
        hybrid_results: List[Dict[str, Any]],
        kg_results: List[Dict[str, Any]],
        kg_weight: float = 0.3,
    ) -> List[Dict[str, Any]]:
        if not kg_results:
            return hybrid_results
        
        results_map: Dict[str, Dict[str, Any]] = {}
        
        for i, result in enumerate(hybrid_results):
            chunk_id = result.get("chunk_id")
            if chunk_id:
                result["hybrid_score"] = result.get(
                    "rerank_score", result.get("rrf_score", 0)
                )
                result["hybrid_rank"] = i
                results_map[chunk_id] = result
        
        for i, result in enumerate(kg_results):
            chunk_id = result.get("chunk_id")
            if chunk_id:
                kg_similarity = result.get("kg_similarity", 0)
                
                if chunk_id in results_map:
                    existing = results_map[chunk_id]
                    hybrid_score = existing.get("hybrid_score", 0)
                    fused_score = (
                        (1 - kg_weight) * hybrid_score +
                        kg_weight * kg_similarity
                    )
                    existing["fused_score"] = fused_score
                    existing["kg_enhanced"] = True
                else:
                    result["fused_score"] = kg_weight * kg_similarity
                    result["kg_enhanced"] = False
                    results_map[chunk_id] = result
        
        fused = list(results_map.values())
        fused.sort(
            key=lambda x: x.get("fused_score", x.get("hybrid_score", 0)),
            reverse=True
        )
        
        return fused
