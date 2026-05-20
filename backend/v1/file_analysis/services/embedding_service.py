from typing import List, Optional, Dict, Any
import requests
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

    def detect_vector_dimension(self, test_text: str = "Hello, world!") -> int:
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
        if EmbeddingService._vector_dim is None:
            return self.detect_vector_dimension()
        return EmbeddingService._vector_dim

    def check_ollama_compatible(self) -> bool:
        base_url = config.embedding.BASE_URL
        return "ollama" in base_url.lower() or "11434" in base_url

    def encode(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        valid_indices = [i for i, t in enumerate(texts) if t and t.strip()]
        valid_texts = [texts[i] for i in valid_indices]

        if not valid_texts:
            return [[0.0] * config.embedding.DIMENSIONS for _ in texts]

        dimensions = config.embedding.DIMENSIONS
        is_ollama = self.check_ollama_compatible()
        batch_size = config.embedding.BATCH_SIZE

        try:
            if is_ollama:
                valid_embeddings = self._encode_ollama(valid_texts)
            elif len(valid_texts) <= batch_size:
                valid_embeddings = self._encode_openai(valid_texts, dimensions)
            else:
                valid_embeddings = self._encode_openai_batched(valid_texts, dimensions, batch_size)

        except Exception as e:
            logger.error(f"Embedding encode failed: {e}")
            raise

        zero_vec = [0.0] * (len(valid_embeddings[0]) if valid_embeddings else dimensions)
        result = [zero_vec[:] for _ in texts]
        for idx, emb in zip(valid_indices, valid_embeddings):
            result[idx] = emb
        return result

    def _encode_openai(self, texts: List[str], dimensions: int) -> List[List[float]]:
        response = EmbeddingService._client.embeddings.create(
            input=texts,
            model=config.embedding.MODEL,
            dimensions=dimensions
        )

        embeddings = [item.embedding for item in response.data]
        logger.info(f"[EmbeddingService] OpenAI接口生成 {len(embeddings)} 个向量，维度: {dimensions}")
        return embeddings

    def _encode_openai_batched(self, texts: List[str], dimensions: int, batch_size: int) -> List[List[float]]:
        total = len(texts)
        batches = [texts[i:i + batch_size] for i in range(0, total, batch_size)]
        logger.info(f"[EmbeddingService] 分批处理: {total} 条文本, 分 {len(batches)} 批, 每批 {batch_size} 条")

        all_embeddings: List[Optional[List[List[float]]]] = [None] * len(batches)
        max_workers = min(4, len(batches))
        max_retries = config.embedding.MAX_RETRIES

        def process_batch(batch_idx: int, batch_texts: List[str]) -> tuple:
            for attempt in range(max_retries):
                try:
                    response = EmbeddingService._client.embeddings.create(
                        input=batch_texts,
                        model=config.embedding.MODEL,
                        dimensions=dimensions
                    )
                    return batch_idx, [item.embedding for item in response.data]
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait = 2 ** attempt
                        logger.warning(f"[EmbeddingService] 批次 {batch_idx} 第 {attempt+1} 次失败，{wait}s 后重试: {e}")
                        time.sleep(wait)
                    else:
                        logger.error(f"[EmbeddingService] 批次 {batch_idx} 重试 {max_retries} 次后仍失败: {e}")
                        raise

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(process_batch, idx, batch): idx
                for idx, batch in enumerate(batches)
            }
            for future in as_completed(futures):
                batch_idx, result = future.result()
                all_embeddings[batch_idx] = result

        embeddings = []
        for batch_result in all_embeddings:
            if batch_result:
                embeddings.extend(batch_result)

        logger.info(f"[EmbeddingService] 分批完成: 共生成 {len(embeddings)} 个向量，维度: {dimensions}")
        return embeddings

    def _encode_ollama(self, texts: List[str]) -> List[List[float]]:
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
