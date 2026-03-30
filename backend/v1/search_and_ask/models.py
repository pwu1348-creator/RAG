from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    knowledge_base_id: str
    top_k: Optional[int] = 10
    min_score: Optional[float] = 0.3
    use_hybrid: Optional[bool] = True


class ChatRequest(BaseModel):
    query: str
    knowledge_base_id: str
    chat_history: Optional[List[Dict[str, str]]] = None
    top_k: Optional[int] = 10
    min_score: Optional[float] = 0.3
    is_write_mode: Optional[bool] = False
    max_context_chars: Optional[int] = 8000


class AskResponse(BaseModel):
    answer: str
    citations: List[Dict[str, Any]]
    search_results: List[Dict[str, Any]]
    timestamp: str


class WriteChatRequest(BaseModel):
    query: str
    knowledge_base_id: str
    document_context: Optional[str] = None
    top_k: Optional[int] = 10
    min_score: Optional[float] = 0.3
    max_context_chars: Optional[int] = 8000
