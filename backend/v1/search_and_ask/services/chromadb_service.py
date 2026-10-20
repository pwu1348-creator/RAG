import json
import chromadb
from typing import List, Dict, Any, Optional

from config import config
from utils.logger import logger


class ChromaDBService:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._is_persistent = not config.chromadb.HOST
        self.client = chromadb.HttpClient(
            host=config.chromadb.HOST,
            port=config.chromadb.PORT
        ) if config.chromadb.HOST else chromadb.PersistentClient(
            path=config.chromadb.PERSIST_DIRECTORY
        )

        self._collections: Dict[str, Any] = {}
        logger.info("[ChromaDB-Search] 服务初始化完成")

    def reload_client(self):
        """重新加载 PersistentClient，刷新 HNSW 内存索引以读取最新写入。"""
        if not self._is_persistent:
            return
        self.client = chromadb.PersistentClient(
            path=config.chromadb.PERSIST_DIRECTORY
        )
        self._collections.clear()
        logger.info("[ChromaDB-Search] PersistentClient 已重新加载，HNSW 索引已刷新")

    def _get_collection_name(self, tenant_id: str) -> str:
        return f"pengpengrag_{tenant_id}"

    def get_collection(self, tenant_id: str):
        collection_name = self._get_collection_name(tenant_id)

        if collection_name in self._collections:
            return self._collections[collection_name]

        try:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            self._collections[collection_name] = collection
            logger.info(f"[ChromaDB-Search] 使用 collection: {collection_name}")
            return collection
        except Exception as e:
            logger.error(f"[ChromaDB-Search] 获取 collection 失败: {e}")
            raise

    def invalidate_collection(self, tenant_id: str):
        collection_name = self._get_collection_name(tenant_id)
        self._collections.pop(collection_name, None)

    def reload_client(self):
        self._collections.clear()
        self.client = chromadb.HttpClient(
            host=config.chromadb.HOST,
            port=config.chromadb.PORT
        ) if config.chromadb.HOST else chromadb.PersistentClient(
            path=config.chromadb.PERSIST_DIRECTORY
        )
        logger.info("[ChromaDB-Search] 客户端已重新加载")

    def search(
        self,
        tenant_id: str,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        collection = self.get_collection(tenant_id)
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filters,
            )

            documents = []
            for i in range(len(results["ids"][0])):
                meta = results["metadatas"][0][i]
                documents.append({
                    "id": results["ids"][0][i],
                    "content_with_weight": results["documents"][0][i],
                    "metadata": {
                        "doc_id": meta.get("doc_id", ""),
                        "kb_id": meta.get("kb_id", ""),
                        "docnm_kwd": meta.get("docnm_kwd", ""),
                        "title_tks": meta.get("title_tks", ""),
                        "title_sm_tks": meta.get("title_sm_tks", ""),
                        "content_ltks": meta.get("content_ltks", ""),
                        "content_sm_ltks": meta.get("content_sm_ltks", ""),
                        "page_num_int": json.loads(meta.get("page_num_int", "[]")),
                        "position_int": json.loads(meta.get("position_int", "[]")),
                        "top_int": json.loads(meta.get("top_int", "[1]")),
                        "create_time": meta.get("create_time", ""),
                        "create_timestamp_flt": meta.get("create_timestamp_flt", 0.0),
                        "img_id": meta.get("img_id", ""),
                    },
                    "distance": results["distances"][0][i] if "distances" in results else None,
                })

            return documents

        except Exception as e:
            logger.error(f"[ChromaDB-Search] 检索失败: {e}")
            raise

    def search_by_text(
        self,
        tenant_id: str,
        query_text: str,
        top_k: int = 5,
        filters: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        collection = self.get_collection(tenant_id)
        try:
            results = collection.query(
                query_texts=[query_text],
                n_results=top_k,
                where=filters,
            )

            documents = []
            for i in range(len(results["ids"][0])):
                meta = results["metadatas"][0][i]
                documents.append({
                    "id": results["ids"][0][i],
                    "content_with_weight": results["documents"][0][i],
                    "metadata": meta,
                    "distance": results["distances"][0][i] if "distances" in results else None,
                })

            return documents

        except Exception as e:
            logger.error(f"[ChromaDB-Search] 全文检索失败: {e}")
            raise
