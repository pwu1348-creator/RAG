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
