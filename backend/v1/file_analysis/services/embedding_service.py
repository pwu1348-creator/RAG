from typing import List, Optional, Dict, Any
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

    def detect_vector_dimension(self, test_text: str = "Hello, world!") -> int:
        """检测embedding向量的维度"""
        if EmbeddingService._vector_dim is not None:
            return EmbeddingService._vector_dim

        try:
            result = self.encode_single(test_text)
            dim = len(result)
            EmbeddingService._vector_dim = dim
            logger.info(f"[EmbeddingService] 检测到向量维度: {dim}")
            return dim
        except Exception as e:
            logger.warning(f"[EmbeddingService] 检测向量维度失败，使用默认维度: {e}")
            return config.embedding.DIMENSIONS

    def get_vector_dimension(self) -> int:
        """获取当前向量维度"""
        if EmbeddingService._vector_dim is None:
            return self.detect_vector_dimension()
        return EmbeddingService._vector_dim

    def check_ollama_compatible(self) -> bool:
        """检查是否是Ollama兼容接口"""
        base_url = config.embedding.BASE_URL
        return "ollama" in base_url.lower() or "11434" in base_url

    def encode(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        dimensions = config.embedding.DIMENSIONS
        is_ollama = self.check_ollama_compatible()

        try:
            if is_ollama:
                return self._encode_ollama(texts)
            else:
                return self._encode_openai(texts, dimensions)

        except Exception as e:
            logger.error(f"Embedding encode failed: {e}")
            raise

    def _encode_openai(self, texts: List[str], dimensions: int) -> List[List[float]]:
        """使用OpenAI兼容接口"""
        response = EmbeddingService._client.embeddings.create(
            input=texts,
            model=config.embedding.MODEL,
            dimensions=dimensions
        )

        embeddings = [item.embedding for item in response.data]
        logger.info(f"[EmbeddingService] OpenAI接口生成 {len(embeddings)} 个向量，维度: {dimensions}")
        return embeddings

    def _encode_ollama(self, texts: List[str]) -> List[List[float]]:
        """使用Ollama接口"""
        embeddings = []
        base_url = config.embedding.BASE_URL.rstrip('/')
        
        for text in texts:
            try:
                response = requests.post(
                    f"{base_url}/api/embeddings",
                    json={
                        "model": config.embedding.MODEL,
                        "prompt": text
                    },
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()
                embedding = result.get("embedding", [])
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"[EmbeddingService] Ollama encode failed for text: {e}")
                embeddings.append([])
        
        if embeddings and embeddings[0]:
            dim = len(embeddings[0])
            logger.info(f"[EmbeddingService] Ollama接口生成 {len(embeddings)} 个向量，维度: {dim}")
        
        return embeddings

    def encode_single(self, text: str) -> List[float]:
        result = self.encode([text])
        return result[0] if result else []
