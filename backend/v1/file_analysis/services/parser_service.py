import os
import json
import threading
from datetime import datetime
from typing import Optional, Dict, List, Any
from concurrent.futures import ThreadPoolExecutor

from config import config
from models.task import ParseTask, TaskStatus
from models.document import DocumentMetadata
from utils.logger import logger
from services.minio_service import MinIOService
from services.mysql_service import MySQLService
from services.chromadb_service import ChromaDBService
from services.embedding_service import EmbeddingService
from core.document_parser import DocumentParser, DocumentProcessor


class ParserService:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.tasks: Dict[str, ParseTask] = {}
        self.document_parser = DocumentParser()
        self.document_processor = DocumentProcessor()
        self.minio = MinIOService()
        self.mysql = MySQLService()
        self.chromadb = ChromaDBService()
        self.embedding = EmbeddingService()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._lock = threading.RLock()
    
    def create_task(
        self,
        task_id: str,
        filename: str,
        file_path: str,
        options: str = '{}',
        kb_id: Optional[str] = None,
        doc_id: Optional[str] = None
    ) -> ParseTask:
        try:
            parse_options = json.loads(options) if isinstance(options, str) else options
        except json.JSONDecodeError:
            parse_options = {}
        
        task = ParseTask(
            task_id=task_id,
            filename=filename,
            file_path=file_path,
            options=parse_options,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            progress=0,
            doc_id=doc_id,
            knowledge_base_id=kb_id
        )
        
        with self._lock:
            self.tasks[task_id] = task
        
        self.executor.submit(
            self._process_task,
            task,
            kb_id,
            doc_id
        )
        
        return task
    
    def _process_task(
        self,
        task: ParseTask,
        kb_id: Optional[str] = None,
        doc_id: Optional[str] = None
    ):
        file_id = doc_id or task.doc_id
        
        try:
            task.status = TaskStatus.PROCESSING
            task.started_at = datetime.now()
            task.progress = 10
            
            logger.info(f"Processing task: {task.task_id}, file: {task.filename}, doc_id: {doc_id}")
            
            if file_id:
                existing_doc = self.mysql.get_document(file_id)
                if existing_doc:
                    self.mysql.update_document(file_id, status='processing')
                    logger.info(f"Using existing document: {file_id}")
            
            task.progress = 30
            
            parse_result = self.document_processor.process_document(
                file_path=task.file_path,
                file_id=file_id,
                kb_id=kb_id,
                options=task.options,
                progress_callback=lambda p: self._update_progress(task, p)
            )
            
            chunks = parse_result.get('chunks', [])
            
            task.progress = 100
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = parse_result
            
            logger.info(f"Task completed: {task.task_id}, doc_id: {doc_id}")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            
            if file_id:
                self.mysql.update_document_status(file_id, "failed")
            
            if kb_id and file_id:
                self.mysql.update_kb_document_status(kb_id, file_id, 'failed', 0)
            
            logger.error(f"Task failed: {task.task_id}, error: {str(e)}")
    
    def _update_progress(self, task: ParseTask, progress: int):
        task.progress = 40 + int(progress * 0.3)
    
    def get_task(self, task_id: str) -> Optional[ParseTask]:
        with self._lock:
            return self.tasks.get(task_id)
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        return self.mysql.get_document(doc_id)
    
    def delete_task(self, task_id: str) -> bool:
        with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return False
            
            if task.doc_id:
                # Delete from MySQL
                self.mysql.delete_document(task.doc_id)
                # Delete from ChromaDB
                self.chromadb.delete_document_chunks(task.doc_id)
            
            # Delete from local storage
            if task.minio_url:
                object_name = f"{task.task_id}/{task.filename}"
                try:
                    self.minio.delete_file(object_name)
                except:
                    pass
            
            # Delete local file
            if os.path.exists(task.file_path):
                os.remove(task.file_path)
            
            del self.tasks[task_id]
            
            return True
    
    def list_tasks(
        self,
        status: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> Dict[str, Any]:
        with self._lock:
            tasks = list(self.tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status.value == status]
        
        tasks.sort(key=lambda x: x.created_at, reverse=True)
        
        total = len(tasks)
        start = (page - 1) * size
        end = start + size
        
        return {
            'total': total,
            'page': page,
            'size': size,
            'tasks': [t.to_dict() for t in tasks[start:end]]
        }
    
    def list_documents(
        self,
        user_id: Optional[str] = None,
        knowledge_base_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> Dict[str, Any]:
        return self.mysql.list_documents(user_id, knowledge_base_id, status, page, size)
