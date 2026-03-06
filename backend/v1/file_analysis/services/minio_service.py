import os
import shutil
from typing import Optional
from config import config
from utils.logger import logger


class MinIOService:
    """文件存储服务（暂时使用本地存储替代MinIO）"""
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
        self.storage_path = config.storage.LOCAL_PATH
        os.makedirs(self.storage_path, exist_ok=True)
        logger.info(f"Local storage initialized: {self.storage_path}")

    def upload_file(self, file_path: str, object_name: Optional[str] = None) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if object_name is None:
            object_name = os.path.basename(file_path)

        dest_path = os.path.join(self.storage_path, object_name)
        shutil.copy2(file_path, dest_path)

        logger.info(f"File saved locally: {object_name}")
        return f"local://{object_name}"

    def download_file(self, object_name: str, file_path: str):
        source_path = os.path.join(self.storage_path, object_name)
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"File not found: {object_name}")

        shutil.copy2(source_path, file_path)
        logger.info(f"File copied: {object_name}")

    def delete_file(self, object_name: str):
        file_path = os.path.join(self.storage_path, object_name)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"File deleted: {object_name}")

    def get_file_path(self, object_name: str) -> str:
        return os.path.join(self.storage_path, object_name)
