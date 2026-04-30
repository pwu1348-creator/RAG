import os
from dataclasses import dataclass, field
from typing import List, Dict, Any
from pathlib import Path

# 加载统一配置文件 backend/v1/.env（在 Config 实例化之前）
_env_path = Path(__file__).parent.parent.parent / ".env"
if _env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_path, override=False)
    except ImportError:
        pass  # python-dotenv 未安装时跳过，使用代码默认值


@dataclass
class ParserConfig:
    SUPPORTED_EXTENSIONS: List[str] = field(default_factory=lambda: [
        '.pdf', '.docx', '.doc', '.txt', '.md', '.json', '.csv', '.xlsx', '.xls', '.pptx', '.ppt', 
        '.png', '.jpg', '.jpeg', '.gif'
    ])
    MAX_FILE_SIZE: int = 50
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200


# MinIO配置（暂时禁用，使用本地存储）
# @dataclass
# class MinIOConfig:
#     ENDPOINT: str = "localhost:9000"
#     ACCESS_KEY: str = "admin"
#     SECRET_KEY: str = "wushipeng"
#     BUCKET_NAME: str = "documents"
#     SECURE: bool = False

@dataclass
class StorageConfig:
    TYPE: str = "local"  # local 或 minio
    LOCAL_PATH: str = "./uploads"
    # MinIO配置（暂时禁用）
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "admin"
    MINIO_SECRET_KEY: str = "wushipeng"
    MINIO_BUCKET: str = "documents"


@dataclass
class ChromaDBConfig:
    # 设置为null或空字符串使用本地持久化模式（无需启动服务）
    HOST: str = ""  # 空字符串表示使用本地持久化模式
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
    # 解析引擎: pipeline（管道普通模式）、vlm（VLM模式）、hybrid（混合模式）
    PARSE_ENGINE: str = "pipeline"


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
    DIMENSIONS: int = 1024
    BATCH_SIZE: int = 32
    MAX_RETRIES: int = 3


@dataclass
class ModelConfig:
    EMBEDDING_MODEL: str = "Qwen3-Embedding-8B"
    EMBEDDING_DEVICE: str = "cpu"
    VECTOR_DIMENSION: int = 1024
    BATCH_SIZE: int = 32


class Config:
    def __init__(self):
        self.parser = ParserConfig()
        self.storage = StorageConfig()  # 使用本地存储配置
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
        
        # 存储配置
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
        self.parser.CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', self.parser.CHUNK_SIZE))
        
        # MinerU 解析引擎配置
        self.mineru.PARSE_ENGINE = os.getenv('MINERU_PARSE_ENGINE', self.mineru.PARSE_ENGINE)
        
        self.embedding.BASE_URL = os.getenv('EMBEDDING_BASE_URL', self.embedding.BASE_URL)
        self.embedding.API_KEY = os.getenv('EMBEDDING_API_KEY', self.embedding.API_KEY)
        self.embedding.MODEL = os.getenv('EMBEDDING_MODEL', self.embedding.MODEL)
        self.embedding.DIMENSIONS = int(os.getenv('EMBEDDING_DIMENSIONS', self.embedding.DIMENSIONS))
        
        self.model.EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', self.model.EMBEDDING_MODEL)
        
        self.admin.DEFAULT_USERNAME = os.getenv('ADMIN_DEFAULT_USERNAME', self.admin.DEFAULT_USERNAME)
        self.admin.DEFAULT_PASSWORD = os.getenv('ADMIN_DEFAULT_PASSWORD', self.admin.DEFAULT_PASSWORD)
        self.admin.DEFAULT_EMAIL = os.getenv('ADMIN_DEFAULT_EMAIL', self.admin.DEFAULT_EMAIL)

        # JWT 配置
        self.jwt.SECRET_KEY = os.getenv('JWT_SECRET_KEY', self.jwt.SECRET_KEY)
        self.jwt.ALGORITHM = os.getenv('JWT_ALGORITHM', self.jwt.ALGORITHM)
        self.jwt.ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv('JWT_EXPIRE_HOURS', self.jwt.ACCESS_TOKEN_EXPIRE_HOURS))


config = Config()
