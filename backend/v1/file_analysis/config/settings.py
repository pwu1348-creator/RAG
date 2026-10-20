import os
from dataclasses import dataclass, field
from typing import List, Dict, Any
from pathlib import Path

_env_path = Path(__file__).parent.parent.parent / ".env"
if _env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_path, override=False)
    except ImportError:
        pass


@dataclass
class ParserConfig:
    SUPPORTED_EXTENSIONS: List[str] = field(default_factory=lambda: [
        '.pdf', '.docx', '.doc', '.txt', '.md', '.json', '.csv', '.xlsx', '.xls', '.pptx', '.ppt', 
        '.png', '.jpg', '.jpeg', '.gif'
    ])
    MAX_FILE_SIZE: int = 50


@dataclass
class StorageConfig:
    TYPE: str = "local"
    LOCAL_PATH: str = "./uploads"
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "admin"
    MINIO_SECRET_KEY: str = "wushipeng"
    MINIO_BUCKET: str = "documents"


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
    POOL_SIZE: int = 10


@dataclass
class MinerUConfig:
    ENABLE_OCR: bool = True
    OCR_LANGUAGE: str = "ch_sim"
    PARSE_ENGINE: str = "pipeline"
    API_TOKEN: str = ""
    API_BASE_URL: str = "https://mineru.net/api/v4"
    FILE_URL_PREFIX: str = "https://rag.zhou1028.cn/uploads"
    POLL_INTERVAL: int = 5
    POLL_TIMEOUT: int = 300


@dataclass
class APIConfig:
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: List[str] = field(default_factory=lambda: ["*"])
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = field(default_factory=lambda: ["*"])
    CORS_ALLOW_HEADERS: List[str] = field(default_factory=lambda: ["*"])
    API_PREFIX: str = "/api/v1"


@dataclass
class AdminConfig:
    DEFAULT_USERNAME: str = "admin"
    DEFAULT_PASSWORD: str = "wushipeng"
    DEFAULT_EMAIL: str = "admin@example.com"
    DEFAULT_ROLE: str = "super_admin"


@dataclass
class JWTConfig:
    SECRET_KEY: str = field(default_factory=lambda: os.getenv('JWT_SECRET_KEY', 'pengpeng-rag-jwt-secret-key-2024'))
    ALGORITHM: str = field(default_factory=lambda: os.getenv('JWT_ALGORITHM', 'HS256'))
    ACCESS_TOKEN_EXPIRE_HOURS: int = field(default_factory=lambda: int(os.getenv('JWT_EXPIRE_HOURS', '24')))


@dataclass
class EmbeddingConfig:
    BASE_URL: str = "https://ai.gitee.com/v1"
    API_KEY: str = "MG6HEPE9JFLDHXJYUR0S6BNA5CUAX7X9N99KLPU4"
    MODEL: str = "Qwen3-Embedding-8B"
    DIMENSIONS: int = 4096
    BATCH_SIZE: int = 32
    MAX_RETRIES: int = 3


@dataclass
class ModelConfig:
    EMBEDDING_MODEL: str = "Qwen3-Embedding-8B"
    EMBEDDING_DEVICE: str = "cpu"
    VECTOR_DIMENSION: int = 4096
    BATCH_SIZE: int = 32


class Config:
    def __init__(self):
        self.parser = ParserConfig()
        self.storage = StorageConfig()
        self.chromadb = ChromaDBConfig()
        self.mysql = MySQLConfig()
        self.mineru = MinerUConfig()
        self.embedding = EmbeddingConfig()
        self.api = APIConfig()
        self.model = ModelConfig()
        self.admin = AdminConfig()
        self.jwt = JWTConfig()
        self._load_from_env()
    
    def _load_from_env(self):
        self.api.HOST = os.getenv('FILE_ANALYSIS_HOST', self.api.HOST)
        self.api.DEBUG = os.getenv('FILE_ANALYSIS_DEBUG', 'False').lower() == 'true'
        self.api.LOG_LEVEL = os.getenv('FILE_ANALYSIS_LOG_LEVEL', self.api.LOG_LEVEL)
        
        self.storage.TYPE = os.getenv('STORAGE_TYPE', self.storage.TYPE)
        self.storage.LOCAL_PATH = os.getenv('STORAGE_LOCAL_PATH', self.storage.LOCAL_PATH)
        
        self.chromadb.HOST = os.getenv('CHROMADB_HOST', self.chromadb.HOST)
        self.chromadb.PORT = int(os.getenv('CHROMADB_PORT', self.chromadb.PORT))
        self.chromadb.COLLECTION_NAME = os.getenv('CHROMADB_COLLECTION', self.chromadb.COLLECTION_NAME)
        
        self.mysql.HOST = os.getenv('MYSQL_HOST', self.mysql.HOST)
        self.mysql.PORT = int(os.getenv('MYSQL_PORT', self.mysql.PORT))
        self.mysql.USER = os.getenv('MYSQL_USER', self.mysql.USER)
        self.mysql.PASSWORD = os.getenv('MYSQL_PASSWORD', self.mysql.PASSWORD)
        self.mysql.DATABASE = os.getenv('MYSQL_DATABASE', self.mysql.DATABASE)
        
        self.parser.MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE_MB', self.parser.MAX_FILE_SIZE))
        
        self.mineru.PARSE_ENGINE = os.getenv('MINERU_PARSE_ENGINE', self.mineru.PARSE_ENGINE)
        self.mineru.API_TOKEN = os.getenv('MINERU_API_TOKEN', self.mineru.API_TOKEN)
        self.mineru.API_BASE_URL = os.getenv('MINERU_API_BASE_URL', self.mineru.API_BASE_URL)
        self.mineru.FILE_URL_PREFIX = os.getenv('MINERU_FILE_URL_PREFIX', self.mineru.FILE_URL_PREFIX)
        self.mineru.POLL_INTERVAL = int(os.getenv('MINERU_POLL_INTERVAL', self.mineru.POLL_INTERVAL))
        self.mineru.POLL_TIMEOUT = int(os.getenv('MINERU_POLL_TIMEOUT', self.mineru.POLL_TIMEOUT))
        
        self.embedding.BASE_URL = os.getenv('EMBEDDING_BASE_URL', self.embedding.BASE_URL)
        self.embedding.API_KEY = os.getenv('EMBEDDING_API_KEY', self.embedding.API_KEY)
        self.embedding.MODEL = os.getenv('EMBEDDING_MODEL', self.embedding.MODEL)
        self.embedding.DIMENSIONS = int(os.getenv('EMBEDDING_DIMENSIONS', self.embedding.DIMENSIONS))
        
        self.model.EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', self.model.EMBEDDING_MODEL)
        
        self.admin.DEFAULT_USERNAME = os.getenv('ADMIN_DEFAULT_USERNAME', self.admin.DEFAULT_USERNAME)
        self.admin.DEFAULT_PASSWORD = os.getenv('ADMIN_DEFAULT_PASSWORD', self.admin.DEFAULT_PASSWORD)
        self.admin.DEFAULT_EMAIL = os.getenv('ADMIN_DEFAULT_EMAIL', self.admin.DEFAULT_EMAIL)

        self.jwt.SECRET_KEY = os.getenv('JWT_SECRET_KEY', self.jwt.SECRET_KEY)
        self.jwt.ALGORITHM = os.getenv('JWT_ALGORITHM', self.jwt.ALGORITHM)
        self.jwt.ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv('JWT_EXPIRE_HOURS', self.jwt.ACCESS_TOKEN_EXPIRE_HOURS))


config = Config()
