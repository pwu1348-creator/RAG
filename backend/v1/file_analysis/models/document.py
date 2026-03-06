from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class DocumentMetadata:
    doc_id: str
    filename: str
    file_type: str
    file_size: int
    minio_url: str
    minio_bucket: str
    minio_object: str
    total_pages: int = 0
    total_chunks: int = 0
    text_length: int = 0
    status: str = "processing"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None
    knowledge_base_id: Optional[str] = None
    extra_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'doc_id': self.doc_id,
            'filename': self.filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'minio_url': self.minio_url,
            'minio_bucket': self.minio_bucket,
            'minio_object': self.minio_object,
            'total_pages': self.total_pages,
            'total_chunks': self.total_chunks,
            'text_length': self.text_length,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user_id': self.user_id,
            'knowledge_base_id': self.knowledge_base_id,
            'extra_metadata': self.extra_metadata
        }


@dataclass
class DocumentChunk:
    chunk_id: str
    doc_id: str
    content: str
    embedding: Optional[List[float]] = None
    chunk_index: int = 0
    page_number: int = 0
    start_pos: int = 0
    end_pos: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'chunk_id': self.chunk_id,
            'doc_id': self.doc_id,
            'content': self.content,
            'chunk_index': self.chunk_index,
            'page_number': self.page_number,
            'start_pos': self.start_pos,
            'end_pos': self.end_pos
        }
