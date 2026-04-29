from typing import List, Optional
import requests
from openai import OpenAI

from config import config
from utils.logger import logger


class EmbeddingService:
    _instance = None
    _client = None
    _vector_dim: Optional[int] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._init_client()

    def _init_client(self):
        if EmbeddingService._client is None:
            logger.info(f"Initializing Embedding client: {config.embedding.BASE_URL}")
            EmbeddingService._client = OpenAI(
                base_url=config.embedding.BASE_URL,
                api_key=config.embedding.API_KEY,
                default_headers={"X-Failover-Enabled": "true"}
            )

    def encode(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        try:
            response = EmbeddingService._client.embeddings.create(
                input=texts,
                model=config.embedding.MODEL,
                dimensions=config.embedding.DIMENSIONS
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Embedding encode failed: {e}")
            raise

    def encode_single(self, text: str) -> List[float]:
        result = self.encode([text])
        return result[0] if result else []
