import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from services.chromadb_service import ChromaDBService
from services.mysql_service import MySQLService
from services.embedding_service import EmbeddingService
from utils.logger import logger
from search_and_ask.retriever import SearchService
from search_and_ask.qa import QuestionAnswering

router = APIRouter()

search_service = SearchService()
qa_service = QuestionAnswering()
chromadb = ChromaDBService()
mysql = MySQLService()
embedding = EmbeddingService()


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


@router.post("/search")
async def search_endpoint(request: SearchRequest):
    """
    检索接口
    """
    try:
        results = search_service.search(
            query=request.query,
            knowledge_base_id=request.knowledge_base_id,
            top_k=request.top_k,
            min_score=request.min_score,
            use_hybrid=request.use_hybrid
        )
        
        return {
            'success': True,
            'results': results,
            'total': len(results)
        }
        
    except Exception as e:
        logger.error(f"[Search API] 检索失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@router.post("/ask")
async def ask_endpoint(request: ChatRequest):
    """
    标准问答接口（非流式）
    """
    try:
        result = await qa_service.chat(
            query=request.query,
            knowledge_base_id=request.knowledge_base_id,
            chat_history=request.chat_history,
            top_k=request.top_k,
            min_score=request.min_score,
            is_write_mode=request.is_write_mode,
            max_context_chars=request.max_context_chars
        )
        
        return result
        
    except Exception as e:
        logger.error(f"[Ask API] 问答失败: {e}")
        return {
            'answer': f"抱歉，处理您的请求时出现错误: {str(e)}",
            'citations': [],
            'search_results': [],
            'timestamp': None
        }


@router.post("/ask/stream")
async def ask_stream_endpoint(request: ChatRequest):
    """
    标准问答接口（流式SSE）
    """
    async def generate_stream():
        try:
            async for chunk in qa_service.chat_stream(
                query=request.query,
                knowledge_base_id=request.knowledge_base_id,
                chat_history=request.chat_history,
                top_k=request.top_k,
                min_score=request.min_score,
                is_write_mode=request.is_write_mode,
                max_context_chars=request.max_context_chars
            ):
                yield f"data: {chunk}\n\n"
        except Exception as e:
            logger.error(f"[Ask Stream API] 流式问答失败: {e}")
            yield f"data: {str(e)}\n\n"
    
    return StreamingResponse(generate_stream(), media_type="text/event-stream")


@router.post("/writechat")
async def writechat_endpoint(request: ChatRequest):
    """
    文档撰写模式问答接口（非流式）
    """
    try:
        result = await qa_service.chat(
            query=request.query,
            knowledge_base_id=request.knowledge_base_id,
            chat_history=request.chat_history,
            top_k=request.top_k,
            min_score=request.min_score,
            is_write_mode=True,
            max_context_chars=request.max_context_chars
        )
        
        return result
        
    except Exception as e:
        logger.error(f"[WriteChat API] 撰写问答失败: {e}")
        return {
            'answer': f"抱歉，处理您的请求时出现错误: {str(e)}",
            'citations': [],
            'search_results': [],
            'timestamp': None
        }


@router.post("/writechat/stream")
async def writechat_stream_endpoint(request: ChatRequest):
    """
    文档撰写模式问答接口（流式SSE）
    """
    async def generate_stream():
        try:
            async for chunk in qa_service.chat_stream(
                query=request.query,
                knowledge_base_id=request.knowledge_base_id,
                chat_history=request.chat_history,
                top_k=request.top_k,
                min_score=request.min_score,
                is_write_mode=True,
                max_context_chars=request.max_context_chars
            ):
                yield f"data: {chunk}\n\n"
        except Exception as e:
            logger.error(f"[WriteChat Stream API] 流式撰写问答失败: {e}")
            yield f"data: {str(e)}\n\n"
    
    return StreamingResponse(generate_stream(), media_type="text/event-stream")


@router.get("/health")
async def health_check():
    """
    健康检查
    """
    return {
        'status': 'healthy',
        'service': 'search-and-ask',
        'version': '1.0.0'
    }
