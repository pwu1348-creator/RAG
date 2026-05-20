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
    """对超过 token 上限的 chunk 强制切分，不做合并。"""
    if not chunks or chunk_token_num <= 0:
        return chunks

    result: List[Dict[str, Any]] = []

    for chunk in chunks:
        if chunk.get("type") == "table":
            result.append(chunk)
            continue

        content = chunk.get("content", "")
        token_count = count_tokens(content)

        if token_count <= chunk_token_num:
            result.append(chunk)
            continue

        # 超过 512 token，按 token 数强制切分
        words = content.split()
        sub_contents = []
        buf = []
        buf_count = 0
        for word in words:
            word_tks = count_tokens(word)
            if buf_count + word_tks > chunk_token_num and buf:
                sub_contents.append(" ".join(buf))
                buf = []
                buf_count = 0
            buf.append(word)
            buf_count += word_tks
        if buf:
            sub_contents.append(" ".join(buf))

        # 如果按空格切不动（中文无空格），按字符估算切分
        if len(sub_contents) <= 1 and token_count > chunk_token_num:
            chars_per_chunk = len(content) * chunk_token_num // token_count
            sub_contents = []
            for i in range(0, len(content), chars_per_chunk):
                seg = content[i:i + chars_per_chunk]
                if seg.strip():
                    sub_contents.append(seg)

        for seg in sub_contents:
            seg_tks = _tokenize_for_count(seg)
            result.append({
                "title_tks":    chunk.get("title_tks", ""),
                "title_sm_tks": chunk.get("title_sm_tks", ""),
                "type":         chunk.get("type", "text"),
                "page_idx":     chunk.get("page_idx", 0),
                "bbox":         chunk.get("bbox", [0, 0, 0, 0]),
                "img_id":       chunk.get("img_id", ""),
                "content":      seg,
                "content_ltks": seg_tks,
                "content_sm_ltks": seg_tks,
            })

    logger.info(
        f"[ParserService] chunk 切分: {len(chunks)} 个原始块 → {len(result)} 个块 "
        f"(上限={chunk_token_num} tokens，仅切分超长块，不合并)"
    )
    return result


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
