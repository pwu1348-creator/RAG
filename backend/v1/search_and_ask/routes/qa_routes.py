"""
问答路由 — 检索 + LLM 生成回答（流式 / 非流式 / 撰写模式）
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from models.schemas import ChatRequest
from core.qa import QuestionAnswering
from utils.logger import logger

router = APIRouter(tags=["问答"])
qa_service = QuestionAnswering()


# ---------------------------------------------------------------------------
# 非流式
# ---------------------------------------------------------------------------

@router.post("/ask")
async def ask_endpoint(request: ChatRequest):
    """标准问答（非流式）"""
    try:
        return await qa_service.chat(
            query=request.query,
            knowledge_base_id=request.knowledge_base_id,
            chat_history=request.chat_history,
            top_k=request.top_k or 10,
            min_score=request.min_score or 0.3,
            is_write_mode=request.is_write_mode if request.is_write_mode is not None else False,
            max_context_chars=request.max_context_chars or 8000,
            use_rerank=request.use_rerank if request.use_rerank is not None else True,
            use_kg=request.use_kg if request.use_kg is not None else True,
            kg_weight=request.kg_weight or 0.3,
        )
    except Exception as e:
        logger.error(f"[Ask API] 问答失败: {e}", exc_info=True)
        return {
            "answer": f"抱歉，处理您的请求时出现错误: {str(e)}",
            "citations": [],
            "search_results": [],
            "timestamp": None,
        }


# ---------------------------------------------------------------------------
# 流式 SSE
# ---------------------------------------------------------------------------

@router.post("/ask/stream")
async def ask_stream_endpoint(request: ChatRequest):
    """标准问答（SSE 流式）"""
    async def generate():
        async for chunk in qa_service.chat_stream(
            query=request.query,
            knowledge_base_id=request.knowledge_base_id,
            chat_history=request.chat_history,
            top_k=request.top_k or 10,
            min_score=request.min_score or 0.3,
            is_write_mode=request.is_write_mode if request.is_write_mode is not None else False,
            max_context_chars=request.max_context_chars or 8000,
            use_rerank=request.use_rerank if request.use_rerank is not None else True,
            use_kg=request.use_kg if request.use_kg is not None else True,
            kg_weight=request.kg_weight or 0.3,
        ):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# 撰写模式
# ---------------------------------------------------------------------------

@router.post("/writechat")
async def writechat_endpoint(request: ChatRequest):
    """撰写模式（非流式）"""
    try:
        return await qa_service.chat(
            query=request.query,
            knowledge_base_id=request.knowledge_base_id,
            chat_history=request.chat_history,
            top_k=request.top_k or 10,
            min_score=request.min_score or 0.3,
            is_write_mode=True,
            max_context_chars=request.max_context_chars or 8000,
            use_rerank=request.use_rerank if request.use_rerank is not None else True,
            use_kg=request.use_kg if request.use_kg is not None else True,
            kg_weight=request.kg_weight or 0.3,
        )
    except Exception as e:
        logger.error(f"[WriteChat API] 撰写问答失败: {e}", exc_info=True)
        return {
            "answer": f"抱歉，处理您的请求时出现错误: {str(e)}",
            "citations": [],
            "search_results": [],
            "timestamp": None,
        }


@router.post("/writechat/stream")
async def writechat_stream_endpoint(request: ChatRequest):
    """撰写模式（SSE 流式）"""
    async def generate():
        async for chunk in qa_service.chat_stream(
            query=request.query,
            knowledge_base_id=request.knowledge_base_id,
            chat_history=request.chat_history,
            top_k=request.top_k or 10,
            min_score=request.min_score or 0.3,
            is_write_mode=True,
            max_context_chars=request.max_context_chars or 8000,
            use_rerank=request.use_rerank if request.use_rerank is not None else True,
            use_kg=request.use_kg if request.use_kg is not None else True,
            kg_weight=request.kg_weight or 0.3,
        ):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
