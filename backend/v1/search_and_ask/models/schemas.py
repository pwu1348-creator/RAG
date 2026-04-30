"""
Pydantic 请求/响应模型
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class SearchRequest(BaseModel):
    """检索请求"""
    query: str
    knowledge_base_id: str
    top_k: Optional[int] = 10
    min_score: Optional[float] = 0.3
    use_hybrid: Optional[bool] = True
    use_rerank: Optional[bool] = True
    use_kg: Optional[bool] = True
    kg_weight: Optional[float] = 0.3


class ChatRequest(BaseModel):
    """问答请求"""
    query: str
    knowledge_base_id: str
    chat_history: Optional[List[Dict[str, str]]] = None
    top_k: Optional[int] = 10
    min_score: Optional[float] = 0.3
    is_write_mode: Optional[bool] = False
    max_context_chars: Optional[int] = 8000
    use_rerank: Optional[bool] = True
    use_kg: Optional[bool] = True
    kg_weight: Optional[float] = 0.3


class AskResponse(BaseModel):
    """问答响应"""
    answer: str
    citations: List[Dict[str, Any]]
    search_results: List[Dict[str, Any]]
    timestamp: str


class WriteChatRequest(BaseModel):
    """撰写模式请求"""
    query: str
    knowledge_base_id: str
    document_context: Optional[str] = None
    top_k: Optional[int] = 10
    min_score: Optional[float] = 0.3
    max_context_chars: Optional[int] = 8000
