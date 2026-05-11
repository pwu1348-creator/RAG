import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import chromadb
from chromadb.config import Settings
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
        self.client = chromadb.HttpClient(
            host=config.chromadb.HOST,
            port=config.chromadb.PORT
        ) if config.chromadb.HOST else chromadb.PersistentClient(
            path=config.chromadb.PERSIST_DIRECTORY
        )

        self._collections: Dict[str, Any] = {}
        logger.info("[ChromaDB] 服务初始化完成")

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
            logger.info(f"[ChromaDB] 使用 collection: {collection_name}")
            return collection
        except Exception as e:
            logger.error(f"[ChromaDB] 获取 collection 失败: {e}")
            raise

    def add_chunks(
        self,
        tenant_id: str,
        doc_id: str,
        kb_id: str,
        chunks: List[Dict[str, Any]],
        embeddings: Optional[List[List[float]]] = None,
        vector_dim: int = 1024,
    ):
        if not chunks:
            return

        collection = self.get_collection(tenant_id)

        try:
            ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]

            documents = [
                chunk.get("content_with_weight", chunk.get("content", ""))
                for chunk in chunks
            ]

            metadatas = []
            for i, chunk in enumerate(chunks):
                metadata = {
                    "doc_id": doc_id,
                    "kb_id": kb_id,
                    "docnm_kwd": chunk.get("docnm_kwd", ""),
                    "title_tks": chunk.get("title_tks", ""),
                    "title_sm_tks": chunk.get("title_sm_tks", ""),
                    "content_ltks": chunk.get("content_ltks", ""),
                    "content_sm_ltks": chunk.get("content_sm_ltks", ""),
                    "page_num_int": json.dumps(chunk.get("page_num_int", []), ensure_ascii=False),
                    "position_int": json.dumps(chunk.get("position_int", []), ensure_ascii=False),
                    "top_int": json.dumps(chunk.get("top_int", [1]), ensure_ascii=False),
                    "create_time": chunk.get("create_time", ""),
                    "create_timestamp_flt": chunk.get("create_timestamp_flt", 0.0),
                    "img_id": chunk.get("img_id", ""),
                    "vector_field": f"q_{vector_dim}_vec",
                }
                metadatas.append(metadata)

            self.collection = collection
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings,
            )

            logger.info(
                f"[ChromaDB] 已存入 {len(chunks)} 个 chunks | "
                f"doc_id={doc_id} | collection=pengpengrag_{tenant_id} | "
                f"vector_field=q_{vector_dim}_vec"
            )

        except Exception as e:
            logger.error(f"[ChromaDB] 存入 chunks 失败: {e}")
            raise

    def delete_document_chunks(self, tenant_id: str, kb_id: str, doc_id: str):
        collection = self.get_collection(tenant_id)
        try:
            collection.delete(
                where={"$and": [{"kb_id": kb_id}, {"doc_id": doc_id}]}
            )
            logger.info(f"[ChromaDB] 已删除文档 chunks: doc_id={doc_id}")
        except Exception as e:
            logger.error(f"[ChromaDB] 删除 chunks 失败: {e}")
            raise

    def delete_collection(self, tenant_id: str):
        collection_name = self._get_collection_name(tenant_id)
        try:
            self.client.delete_collection(name=collection_name)
            self._collections.pop(collection_name, None)
            logger.info(f"[ChromaDB] 已删除 collection: {collection_name}")
        except Exception as e:
            logger.error(f"[ChromaDB] 删除 collection 失败: {e}")
            raise

    def get_document_chunks(self, tenant_id: str, doc_id: str) -> List[Dict[str, Any]]:
        collection = self.get_collection(tenant_id)
        try:
            results = collection.get(where={"doc_id": doc_id})

            chunks = []
            for i in range(len(results["ids"])):
                meta = results["metadatas"][i]
                chunk = {
                    "id": results["ids"][i],
                    "content_with_weight": results["documents"][i],
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
                    "vector_field": meta.get("vector_field", ""),
                }
                chunks.append(chunk)

            return chunks
        except Exception as e:
            logger.error(f"[ChromaDB] 获取 chunks 失败: {e}")
            raise

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
            logger.error(f"[ChromaDB] 检索失败: {e}")
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
            logger.error(f"[ChromaDB] 全文检索失败: {e}")
            raise


chromadb_service = ChromaDBService()
