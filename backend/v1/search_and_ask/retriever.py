import os
import re
import json
import math
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

from config import config
from utils.rag_tokenizer import RagTokenizer
from services.chromadb_service import ChromaDBService
from services.embedding_service import EmbeddingService
from utils.logger import logger


class BM25Retriever:
    """BM25 全文检索器"""
    
    def __init__(self):
        self.tokenizer = RagTokenizer()
        self.documents = []
        self.doc_freq = defaultdict(int)
        self.avg_doc_len = 0
        self.n_docs = 0
        self.bm25_params = {
            'k1': 1.5,
            'b': 0.75
        }
    
    def add_documents(self, docs: List[Dict[str, Any]]):
        """添加文档到索引"""
        self.documents = docs
        self.n_docs = len(docs)
        
        if self.n_docs == 0:
            return
        
        total_len = 0
        
        for doc in docs:
            content = doc.get('content', '') + ' ' + doc.get('text', '')
            tokens = self._tokenize(content)
            total_len += len(tokens)
            
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freq[token] += 1
        
        self.avg_doc_len = total_len / self.n_docs if self.n_docs > 0 else 0
    
    def _tokenize(self, text: str) -> List[str]:
        """分词"""
        return self.tokenizer.tokenize(text).split()
    
    def _bm25_score(self, query_tokens: List[str], doc_tokens: List[str], doc_idx: int) -> float:
        """计算单个文档的BM25分数"""
        score = 0.0
        doc_len = len(doc_tokens)
        freq = defaultdict(int)
        
        for token in doc_tokens:
            freq[token] += 1
        
        for token in query_tokens:
            if token not in freq:
                continue
            
            f = freq[token]
            idf = math.log((self.n_docs - self.doc_freq[token] + 0.5) / (self.doc_freq[token] + 0.5) + 1)
            
            tf = f * (self.bm25_params['k1'] + 1) / (f + self.bm25_params['k1'] * (1 - self.bm25_params['b'] + 
                                 self.bm25_params['b'] * doc_len / self.avg_doc_len))
            
            score += idf * tf
        
        return score
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索"""
        query_tokens = self._tokenize(query)
        
        if not query_tokens or not self.documents:
            return []
        
        scores = []
        for i, doc in enumerate(self.documents):
            content = doc.get('content', '') + ' ' + doc.get('text', '')
            doc_tokens = self._tokenize(content)
            score = self._bm25_score(query_tokens, doc_tokens, i)
            scores.append((i, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for idx, score in scores[:top_k]:
            doc = self.documents[idx].copy()
            doc['bm25_score'] = score
            results.append(doc)
        
        return results


class HybridRetriever:
    """混合检索器：BM25 + 向量检索 + RRF重排序"""
    
    def __init__(self):
        self.bm25 = BM25Retriever()
        self.chromadb = ChromaDBService()
        self.embedding = EmbeddingService()
        self._initialized = False
    
    def initialize(self, knowledge_base_id: str):
        """初始化：从 ChromaDB 加载文档"""
        if self._initialized:
            return
        
        try:
            docs = self.chromadb.get_all_documents(knowledge_base_id)
            self.bm25.add_documents(docs)
            self._initialized = True
            logger.info(f"[HybridRetriever] 初始化完成，加载 {len(docs)} 个文档")
        except Exception as e:
            logger.error(f"[HybridRetriever] 初始化失败: {e}")
            raise
    
    def _rerank_rrf(self, results_bm25: List[Dict], results_vector: List[Dict], 
                   k: int = 60) -> List[Dict]:
        """RRF (Reciprocal Rank Fusion) 重排序"""
        combined_scores = defaultdict(float)
        doc_map = {}
        
        for i, doc in enumerate(results_bm25):
            rank = i + 1
            combined_scores[doc.get('doc_id', '') + '_' + str(doc.get('chunk_index', 0))] += 1 / (k + rank)
            doc_map[doc.get('doc_id', '') + '_' + str(doc.get('chunk_index', 0))] = doc
        
        for i, doc in enumerate(results_vector):
            rank = i + 1
            combined_scores[doc.get('doc_id', '') + '_' + str(doc.get('chunk_index', 0))] += 1 / (k + rank)
            doc_map[doc.get('doc_id', '') + '_' + str(doc.get('chunk_index', 0))] = doc
        
        sorted_docs = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for key, score in sorted_docs[:50]:
            doc = doc_map[key].copy()
            doc['rrf_score'] = score
            results.append(doc)
        
        return results
    
    def _filter_by_similarity(self, results: List[Dict], min_score: float = 0.5) -> List[Dict]:
        """相似度过滤"""
        return [doc for doc in results if doc.get('similarity', 0) >= min_score or 
                doc.get('bm25_score', 0) >= min_score]
    
    def search(self, query: str, knowledge_base_id: str, top_k: int = 10, 
              min_score: float = 0.3) -> List[Dict[str, Any]]:
        """混合搜索"""
        self.initialize(knowledge_base_id)
        
        try:
            query_embedding = self.embedding.encode([query])[0]
        except Exception as e:
            logger.error(f"[HybridRetriever] 向量化失败: {e}")
            query_embedding = None
        
        results_bm25 = self.bm25.search(query, top_k * 2)
        
        results_vector = []
        if query_embedding is not None:
            try:
                vector_results = self.chromadb.search(
                    query=query,
                    top_k=top_k * 2,
                    filters={"kb_id": knowledge_base_id}
                )
                
                for i, doc in enumerate(vector_results):
                    doc['similarity'] = 1 - doc.get('distance', 1)
                    results_vector.append(doc)
            except Exception as e:
                logger.error(f"[HybridRetriever] 向量搜索失败: {e}")
        
        reranked = self._rerank_rrf(results_bm25, results_vector)
        filtered = self._filter_by_similarity(reranked, min_score)
        
        return filtered[:top_k]


class SearchService:
    """检索服务"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.hybrid_retriever = HybridRetriever()
    
    def search(
        self,
        query: str,
        knowledge_base_id: str,
        top_k: int = 10,
        min_score: float = 0.3,
        use_hybrid: bool = True
    ) -> List[Dict[str, Any]]:
        """
        检索接口
        
        Args:
            query: 查询文本
            knowledge_base_id: 知识库ID
            top_k: 返回结果数
            min_score: 最小相似度阈值
            use_hybrid: 是否使用混合检索
            
        Returns:
            检索结果列表
        """
        if use_hybrid:
            return self.hybrid_retriever.search(query, knowledge_base_id, top_k, min_score)
        else:
            self.hybrid_retriever.initialize(knowledge_base_id)
            return self.hybrid_retriever.bm25.search(query, top_k)
