from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ParseTask:
    task_id: str
    filename: str
    file_path: str
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    options: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    minio_url: Optional[str] = None
    doc_id: Optional[str] = None
    knowledge_base_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'filename': self.filename,
            'status': self.status.value,
            'progress': self.progress,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error': self.error,
            'doc_id': self.doc_id
        }
