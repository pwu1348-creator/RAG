import uuid
from typing import List, Dict, Any, Optional
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
        
        self.collection_name = config.chromadb.COLLECTION_NAME
        self.collection = self._get_or_create_collection()
    
    def _get_or_create_collection(self):
        try:
            collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Using collection: {self.collection_name}")
            return collection
        except Exception as e:
            logger.error(f"Collection error: {e}")
            raise
    
    def add_chunks(
        self,
        doc_id: str,
        kb_id: str,
        chunks: List[Dict[str, Any]],
        embeddings: Optional[List[List[float]]] = None
    ):
        if not chunks:
            return
        
        try:
            ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
            texts = [chunk.get('text', chunk.get('content', '')) for chunk in chunks]
            metadatas = [
                {
                    'doc_id': doc_id,
                    'kb_id': kb_id,
                    'chunk_index': i,
                    'page_number': chunk.get('page_number', 0),
                    'start_pos': chunk.get('start', 0),
                    'end_pos': chunk.get('end', 0)
                }
                for i, chunk in enumerate(chunks)
            ]
            
            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas,
                embeddings=embeddings
            )
            
            logger.info(f"Added {len(chunks)} chunks to ChromaDB for doc: {doc_id}")
            
        except Exception as e:
            logger.error(f"Add chunks failed: {e}")
            raise
    
    def delete_document_chunks(self, kb_id: str, doc_id: str):
        try:
            self.collection.delete(
                where={"$and": [{"kb_id": kb_id}, {"doc_id": doc_id}]}
            )
            logger.info(f"Deleted chunks for kb: {kb_id}, doc: {doc_id}")
        except Exception as e:
            logger.error(f"Delete chunks failed: {e}")
            raise
    
    def get_document_chunks(self, doc_id: str) -> List[Dict[str, Any]]:
        try:
            results = self.collection.get(
                where={"doc_id": doc_id}
            )
            
            chunks = []
            for i in range(len(results['ids'])):
                chunks.append({
                    'id': results['ids'][i],
                    'content': results['documents'][i],
                    'metadata': results['metadatas'][i]
                })
            
            return chunks
        except Exception as e:
            logger.error(f"Get document chunks failed: {e}")
            raise
    
    def get_all_documents(self, knowledge_base_id: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            where_filter = None
            if knowledge_base_id:
                where_filter = {"knowledge_base_id": knowledge_base_id}
            
            results = self.collection.get(
                where=where_filter,
                limit=10000
            )
            
            # 按 doc_id 分组
            doc_map = {}
            for i in range(len(results['ids'])):
                metadata = results['metadatas'][i]
                doc_id = metadata.get('doc_id')
                
                if doc_id not in doc_map:
                    doc_map[doc_id] = {
                        'doc_id': doc_id,
                        'chunk_count': 0,
                        'knowledge_base_id': metadata.get('knowledge_base_id'),
                        'filename': metadata.get('filename'),
                        'created_at': metadata.get('created_at')
                    }
                doc_map[doc_id]['chunk_count'] += 1
            
            return list(doc_map.values())
        except Exception as e:
            logger.error(f"Get all documents failed: {e}")
            raise
    
    def delete_collection(self, collection_name: str):
        try:
            self.client.delete_collection(name=collection_name)
            logger.info(f"Deleted collection: {collection_name}")
        except Exception as e:
            logger.error(f"Delete collection failed: {e}")
            raise
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=filters
            )
            
            documents = []
            for i in range(len(results['ids'][0])):
                documents.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise


chromadb_service = ChromaDBService()
