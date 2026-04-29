"""
Search & Ask 独立配置

完全脱离 file_analysis，避免触发 minerU 依赖。
"""

import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class ChromaDBConfig:
    HOST: str = ""
    PORT: int = 8000
    COLLECTION_NAME: str = "document_chunks"
    PERSIST_DIRECTORY: str = "./chroma_db"


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
        self.api = APIConfig()
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


config = Config()
