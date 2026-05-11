"""
Search & Ask 独立配置

完全脱离 file_analysis，避免触发 minerU 依赖。
"""

import os
from dataclasses import dataclass, field
from typing import List
from pathlib import Path

# 加载统一配置文件 backend/v1/.env（在 Config 实例化之前）
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_path, override=False)
    except ImportError:
        pass  # python-dotenv 未安装时跳过，使用代码默认值


@dataclass
class ChromaDBConfig:
    HOST: str = ""
    PORT: int = 8000
    COLLECTION_NAME: str = "document_chunks"
    # 指向 file_analysis 的 chroma_db，确保两个服务共享同一数据库
    PERSIST_DIRECTORY: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "file_analysis", "chroma_db"
    )


@dataclass
class MySQLConfig:
    HOST: str = "localhost"
    PORT: int = 3306
    USER: str = "root"
    PASSWORD: str = "wushipeng"
    DATABASE: str = "rag_system"


@dataclass
class EmbeddingConfig:
    BASE_URL: str = "https://ai.gitee.com/v1"
    API_KEY: str = "MG6HEPE9JFLDHXJYUR0S6BNA5CUAX7X9N99KLPU4"
    MODEL: str = "Qwen3-Embedding-8B"
    DIMENSIONS: int = 1024
    BATCH_SIZE: int = 32
    MAX_RETRIES: int = 3


@dataclass
class LLMConfig:
    BASE_URL: str = "https://ai.gitee.com/v1"
    API_KEY: str = "MG6HEPE9JFLDHXJYUR0S6BNA5CUAX7X9N99KLPU4"
    MODEL: str = "Qwen3-235B-A22B"
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 2048
    TOP_P: float = 0.7
    TOP_K: int = 50
    FREQUENCY_PENALTY: float = 1.0


@dataclass
class RerankerConfig:
    BASE_URL: str = "https://ai.gitee.com/v1/sentence-similarity"
    API_KEY: str = "MG6HEPE9JFLDHXJYUR0S6BNA5CUAX7X9N99KLPU4"
    MODEL: str = "bge-reranker-v2-m3"


@dataclass
class KnowledgeGraphConfig:
    ENABLED: bool = True
    BACKEND: str = "networkx"  # neo4j 或 networkx
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "pengpeng123"
    NEO4J_DATABASE: str = "neo4j"
    EXTRACTION_MODEL: str = "Qwen3-235B-A22B"
    MIN_CONFIDENCE: float = 0.5
    MAX_ENTITIES_PER_DOC: int = 50
    MAX_RELATIONS_PER_DOC: int = 100
    HOP_LIMIT: int = 2
    GRAPH_PERSIST_DIR: str = "./kg_data"


@dataclass
class APIConfig:
    HOST: str = "0.0.0.0"
    PORT: int = 8002
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: List[str] = field(default_factory=lambda: ["*"])
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = field(default_factory=lambda: ["*"])
    CORS_ALLOW_HEADERS: List[str] = field(default_factory=lambda: ["*"])
    API_PREFIX: str = "/api/v1"


class Config:
    def __init__(self):
        self.chromadb = ChromaDBConfig()
        self.mysql = MySQLConfig()
        self.embedding = EmbeddingConfig()
        self.llm = LLMConfig()
        self.reranker = RerankerConfig()
        self.api = APIConfig()
        self.kg = KnowledgeGraphConfig()
        self._load_from_env()

    def _load_from_env(self):
        self.api.HOST = os.getenv('SEARCH_ASK_HOST', self.api.HOST)
        self.api.PORT = int(os.getenv('SEARCH_ASK_PORT', self.api.PORT))
        self.api.DEBUG = os.getenv('SEARCH_ASK_DEBUG', 'False').lower() == 'true'

        self.chromadb.HOST = os.getenv('CHROMADB_HOST', self.chromadb.HOST)
        self.chromadb.PORT = int(os.getenv('CHROMADB_PORT', self.chromadb.PORT))
        self.chromadb.COLLECTION_NAME = os.getenv('CHROMADB_COLLECTION', self.chromadb.COLLECTION_NAME)

        self.mysql.HOST = os.getenv('MYSQL_HOST', self.mysql.HOST)
        self.mysql.PORT = int(os.getenv('MYSQL_PORT', self.mysql.PORT))
        self.mysql.USER = os.getenv('MYSQL_USER', self.mysql.USER)
        self.mysql.PASSWORD = os.getenv('MYSQL_PASSWORD', self.mysql.PASSWORD)
        self.mysql.DATABASE = os.getenv('MYSQL_DATABASE', self.mysql.DATABASE)

        self.embedding.BASE_URL = os.getenv('EMBEDDING_BASE_URL', self.embedding.BASE_URL)
        self.embedding.API_KEY = os.getenv('EMBEDDING_API_KEY', self.embedding.API_KEY)
        self.embedding.MODEL = os.getenv('EMBEDDING_MODEL', self.embedding.MODEL)
        self.embedding.DIMENSIONS = int(os.getenv('EMBEDDING_DIMENSIONS', self.embedding.DIMENSIONS))

        self.llm.BASE_URL = os.getenv('LLM_BASE_URL', self.llm.BASE_URL)
        self.llm.API_KEY = os.getenv('LLM_API_KEY', self.llm.API_KEY)
        self.llm.MODEL = os.getenv('LLM_MODEL', self.llm.MODEL)
        self.llm.TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', self.llm.TEMPERATURE))
        self.llm.MAX_TOKENS = int(os.getenv('LLM_MAX_TOKENS', self.llm.MAX_TOKENS))
        self.llm.TOP_P = float(os.getenv('LLM_TOP_P', self.llm.TOP_P))
        self.llm.TOP_K = int(os.getenv('LLM_TOP_K', self.llm.TOP_K))
        self.llm.FREQUENCY_PENALTY = float(os.getenv('LLM_FREQUENCY_PENALTY', self.llm.FREQUENCY_PENALTY))

        # Reranker 配置
        self.reranker.BASE_URL = os.getenv('RERANKER_BASE_URL', self.reranker.BASE_URL)
        self.reranker.API_KEY = os.getenv('RERANKER_API_KEY', self.reranker.API_KEY)
        self.reranker.MODEL = os.getenv('RERANKER_MODEL', self.reranker.MODEL)

        # Knowledge Graph 配置
        self.kg.ENABLED = os.getenv('KG_ENABLED', 'True').lower() == 'true'
        self.kg.BACKEND = os.getenv('KG_BACKEND', self.kg.BACKEND)
        self.kg.NEO4J_URI = os.getenv('NEO4J_URI', self.kg.NEO4J_URI)
        self.kg.NEO4J_USER = os.getenv('NEO4J_USER', self.kg.NEO4J_USER)
        self.kg.NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', self.kg.NEO4J_PASSWORD)
        self.kg.NEO4J_DATABASE = os.getenv('NEO4J_DATABASE', self.kg.NEO4J_DATABASE)
        self.kg.MIN_CONFIDENCE = float(os.getenv('KG_MIN_CONFIDENCE', self.kg.MIN_CONFIDENCE))
        self.kg.HOP_LIMIT = int(os.getenv('KG_HOP_LIMIT', self.kg.HOP_LIMIT))


config = Config()
