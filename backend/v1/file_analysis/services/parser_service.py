import os
import json
import threading
from datetime import datetime
from typing import Optional, Dict, List, Any, Callable
from concurrent.futures import ThreadPoolExecutor

from config import config
from models.task import ParseTask, TaskStatus
from models.document import DocumentMetadata
from utils.logger import logger
from utils.rag_tokenizer import RagTokenizer
from services.minio_service import MinIOService
from services.mysql_service import MySQLService
from services.chromadb_service import ChromaDBService
from services.embedding_service import EmbeddingService
from core.document_parser import DocumentParser, DocumentProcessor


_tokenizer = RagTokenizer()


def _tokenize_for_count(text: str) -> str:
    try:
        return _tokenizer.tokenize(text)
    except Exception:
        return text


def count_tokens(text: str) -> int:
    tks = _tokenize_for_count(text)
    return len(tks.split()) if tks else 0


def merge_chunks_by_token(
    chunks: List[Dict[str, Any]],
    chunk_token_num: int = 512,
) -> List[Dict[str, Any]]:
    if not chunks or chunk_token_num <= 0:
        return chunks

    merged: List[Dict[str, Any]] = []
    buffer_contents: List[str] = []
    buffer_token_count = 0
    buffer_meta: Optional[Dict[str, Any]] = None

    def _flush():
        nonlocal buffer_contents, buffer_token_count, buffer_meta
        if not buffer_contents or not buffer_meta:
            return
        merged_content = "\n".join(buffer_contents)
        merged_tks = _tokenize_for_count(merged_content)
        merged.append({
            **buffer_meta,
            "content":         merged_content,
            "content_ltks":    merged_tks,
            "content_sm_ltks": merged_tks,
        })
        buffer_contents = []
        buffer_token_count = 0
        buffer_meta = None

    for chunk in chunks:
        if chunk.get("type") == "table":
            _flush()
            merged.append(chunk)
            continue

        content = chunk.get("content", "")
        token_count = count_tokens(content)

        if token_count >= chunk_token_num:
            _flush()
            merged.append(chunk)
            continue

        if buffer_token_count + token_count > chunk_token_num and buffer_contents:
            _flush()

        buffer_contents.append(content)
        buffer_token_count += token_count
        if buffer_meta is None:
            buffer_meta = {
                "title_tks":    chunk.get("title_tks", ""),
                "title_sm_tks": chunk.get("title_sm_tks", ""),
                "type":         chunk.get("type", "text"),
                "page_idx":     chunk.get("page_idx", 0),
                "bbox":         chunk.get("bbox", [0, 0, 0, 0]),
                "img_id":       chunk.get("img_id", ""),
            }

    _flush()

    logger.info(
        f"[ParserService] token 合并: {len(chunks)} 个原始块 → {len(merged)} 个合并块 "
        f"(阈值={chunk_token_num} tokens)"
    )
    return merged


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
        self.sequential_executor = ThreadPoolExecutor(max_workers=1)
        self._lock = threading.RLock()
    
    def create_task(
        self,
        task_id: str,
        filename: str,
        file_path: str,
        options: str = '{}',
        kb_id: Optional[str] = None,
        doc_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        sequential: bool = False,
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

        executor = self.sequential_executor if sequential else self.executor
        executor.submit(
            self._process_task,
            task,
            kb_id,
            doc_id,
            tenant_id,
        )

        return task
    
    def _process_task(
        self,
        task: ParseTask,
        kb_id: Optional[str] = None,
        doc_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
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

            chunk_token_num = task.options.get("chunk_token_num", 512)
            task.options["chunk_merger"] = lambda chunks: merge_chunks_by_token(chunks, chunk_token_num)

            parse_result = self.document_processor.process_document(
                file_path=task.file_path,
                file_id=file_id,
                kb_id=kb_id,
                tenant_id=tenant_id or "",
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
                self.mysql.delete_document(task.doc_id)
                if task.knowledge_base_id:
                    kb = self.mysql.get_knowledge_base(task.knowledge_base_id)
                    tenant_id = kb.get("owner_id", "") if kb else ""
                    if tenant_id:
                        self.chromadb.delete_document_chunks(tenant_id, task.knowledge_base_id, task.doc_id)
            
            if task.minio_url:
                object_name = f"{task.task_id}/{task.filename}"
                try:
                    self.minio.delete_file(object_name)
                except:
                    pass
            
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
