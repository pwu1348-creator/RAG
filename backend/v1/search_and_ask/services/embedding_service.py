from typing import List, Optional
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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

        batch_size = config.embedding.BATCH_SIZE

        try:
            if len(texts) <= batch_size:
                return self._encode_batch(texts)
            else:
                return self._encode_batched(texts, batch_size)
        except Exception as e:
            logger.error(f"Embedding encode failed: {e}")
            raise

    def _encode_batch(self, texts: List[str]) -> List[List[float]]:
        return self._encode_batched(texts, len(texts))

    def _encode_batched(self, texts: List[str], batch_size: int) -> List[List[float]]:
        total = len(texts)
        logger.info(f"[EmbeddingService] 并发处理: {total} 条文本, 维度: {config.embedding.DIMENSIONS}")

        all_embeddings: List[Optional[List[float]]] = [None] * total
        max_workers = min(8, total)
        max_retries = config.embedding.MAX_RETRIES

        def process_single(idx: int, text: str) -> tuple:
            for attempt in range(max_retries):
                try:
                    response = EmbeddingService._client.embeddings.create(
                        input=text,
                        model=config.embedding.MODEL,
                        dimensions=config.embedding.DIMENSIONS
                    )
                    return idx, response.data[0].embedding
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait = 2 ** attempt
                        logger.warning(f"[EmbeddingService] 文本 {idx} 第 {attempt+1} 次失败，{wait}s 后重试: {e}")
                        time.sleep(wait)
                    else:
                        raise

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(process_single, idx, text): idx
                for idx, text in enumerate(texts)
            }
            for future in as_completed(futures):
                idx, embedding = future.result()
                all_embeddings[idx] = embedding

        return [e for e in all_embeddings if e is not None]

    def encode_single(self, text: str) -> List[float]:
        result = self.encode([text])
        return result[0] if result else []
