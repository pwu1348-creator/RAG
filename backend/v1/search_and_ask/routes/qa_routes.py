
import json
import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from models.schemas import ChatRequest
from core.qa import QuestionAnswering, MAX_CONTEXT_CHARS
from services.conversation_service import ConversationService
from utils.logger import logger


def _sse_encode(chunk: str) -> str:
    if '\n' not in chunk:
        return f"data: {chunk}\n\n"
    lines = chunk.split('\n')
    return ''.join(f"data: {line}\n" for line in lines) + "\n"

router = APIRouter(tags=["问答"])
qa_service = QuestionAnswering()
conv_service = ConversationService()


class CreateConversationRequest(BaseModel):
    user_id: str
    kb_id: str
    title: Optional[str] = "新对话"


class UpdateTitleRequest(BaseModel):
    title: str


@router.post("/conversation/create")
async def create_conversation(req: CreateConversationRequest):
    try:
        conv_id = conv_service.create(
            user_id=req.user_id,
            kb_id=req.kb_id,
            title=req.title,
        )
        return {"code": 200, "data": {"conversation_id": conv_id}}
    except Exception as e:
        logger.error(f"[ConvAPI] 创建会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversation/list")
async def list_conversations(user_id: str, page: int = 1, size: int = 50):
    result = conv_service.list_by_user(user_id=user_id, page=page, size=size)
    return {"code": 200, "data": result}


@router.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    conv = conv_service.get(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    messages = conv_service.get_messages(conversation_id)
    return {"code": 200, "data": {**conv, "messages": messages}}


@router.delete("/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str):
    ok = conv_service.delete(conversation_id)
    if not ok:
        raise HTTPException(status_code=404, detail="会话不存在或删除失败")
    return {"code": 200, "message": "删除成功"}


@router.put("/conversation/{conversation_id}/title")
async def update_conversation_title(conversation_id: str, req: UpdateTitleRequest):
    ok = conv_service.update_title(conversation_id, req.title)
    return {"code": 200 if ok else 404, "message": "更新成功" if ok else "会话不存在"}


@router.post("/ask")
async def ask_endpoint(request: ChatRequest):
    try:
        return await qa_service.chat(
            query=request.query,
            knowledge_base_id=request.knowledge_base_id,
            chat_history=request.chat_history,
            top_k=request.top_k or 10,
            min_score=request.min_score or 0.3,
            is_write_mode=request.is_write_mode if request.is_write_mode is not None else False,
            max_context_chars=request.max_context_chars or MAX_CONTEXT_CHARS,
            use_rerank=request.use_rerank if request.use_rerank is not None else True,
            use_kg=request.use_kg if request.use_kg is not None else True,
            kg_weight=request.kg_weight or 0.3,
            answer_mode=request.answer_mode or "strict",
        )
    except Exception as e:
        logger.error(f"[Ask API] 问答失败: {e}", exc_info=True)
        return {
            "answer": f"抱歉，处理您的请求时出现错误: {str(e)}",
            "citations": [],
            "search_results": [],
            "timestamp": None,
        }


class StreamAskRequest(BaseModel):
    query: str
    knowledge_base_id: str
    conversation_id: Optional[str] = None
    chat_history: Optional[list] = None
    top_k: Optional[int] = 10
    min_score: Optional[float] = 0.3
    is_write_mode: Optional[bool] = False
    max_context_chars: Optional[int] = None
    use_rerank: Optional[bool] = True
    use_kg: Optional[bool] = True
    kg_weight: Optional[float] = 0.3
    answer_mode: Optional[str] = "strict"


@router.post("/ask/stream")
async def ask_stream_endpoint(request: StreamAskRequest):
    async def generate():
        if request.conversation_id:
            # 智能记忆加载：优先使用缓存摘要 + 近期消息
            history = qa_service.prepare_history_with_memory(request.conversation_id)
            logger.info(
                f"[AskStream] conv_id={request.conversation_id} "
                f"加载历史 {len(history)} 条（含记忆压缩）"
            )
        else:
            history = request.chat_history or []

        if request.conversation_id:
            conv_service.append_message(
                conversation_id=request.conversation_id,
                role="user",
                content=request.query,
            )
            conv = conv_service.get(request.conversation_id)
            if conv and conv.get("title") == "新对话":
                conv_service.update_title(
                    request.conversation_id,
                    request.query[:40],
                )

        full_answer = ""
        full_thinking = ""
        citations = []
        truncated = False

        async for chunk in qa_service.chat_stream(
            query=request.query,
            knowledge_base_id=request.knowledge_base_id,
            chat_history=history,
            top_k=request.top_k or 10,
            min_score=request.min_score or 0.3,
            is_write_mode=request.is_write_mode if request.is_write_mode is not None else False,
            max_context_chars=request.max_context_chars or MAX_CONTEXT_CHARS,
            use_rerank=request.use_rerank if request.use_rerank is not None else True,
            use_kg=request.use_kg if request.use_kg is not None else True,
            kg_weight=request.kg_weight or 0.3,
            answer_mode=request.answer_mode or "strict",
        ):
            yield _sse_encode(chunk)

            if request.conversation_id:
                if "<!--RAG_META" in chunk:
                    meta_match = chunk.strip()
                    try:
                        import re
                        m = re.search(r'<!--RAG_META\s+([\s\S]*?)\s+RAG_META-->', chunk)
                        if m:
                            meta = json.loads(m.group(1))
                            citations = meta.get("citations", [])
                    except Exception:
                        pass
                elif "\x01" in chunk:
                    import re, base64
                    for b64 in re.findall(r'\x01([A-Za-z0-9+/=]+)\x01', chunk):
                        try:
                            full_thinking += base64.b64decode(b64).decode("utf-8")
                        except Exception:
                            pass
                elif "\x02THINK_END\x02" not in chunk and "<!--RAG_META" not in chunk:
                    full_answer += chunk

        if request.conversation_id and full_answer.strip():
            conv_service.append_message(
                conversation_id=request.conversation_id,
                role="assistant",
                content=full_answer.strip(),
                thinking=full_thinking or None,
                reference=citations or None,
            )
            logger.info(
                f"[AskStream] conv_id={request.conversation_id} "
                f"保存 assistant 消息，长度={len(full_answer)}"
            )
            # 后台异步刷新摘要（不阻塞响应）
            asyncio.ensure_future(
                qa_service.refresh_summary(request.conversation_id)
            )

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/writechat")
async def writechat_endpoint(request: ChatRequest):
    try:
        return await qa_service.chat(
            query=request.query,
            knowledge_base_id=request.knowledge_base_id,
            chat_history=request.chat_history,
            top_k=request.top_k or 10,
            min_score=request.min_score or 0.3,
            is_write_mode=True,
            max_context_chars=request.max_context_chars or MAX_CONTEXT_CHARS,
            use_rerank=request.use_rerank if request.use_rerank is not None else True,
            use_kg=request.use_kg if request.use_kg is not None else True,
            kg_weight=request.kg_weight or 0.3,
            answer_mode=request.answer_mode or "strict",
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
async def writechat_stream_endpoint(request: StreamAskRequest):
    async def generate():
        if request.conversation_id:
            # 智能记忆加载
            history = qa_service.prepare_history_with_memory(request.conversation_id)
        else:
            history = request.chat_history or []

        if request.conversation_id:
            conv_service.append_message(
                conversation_id=request.conversation_id,
                role="user",
                content=request.query,
            )

        full_answer = ""
        citations = []

        async for chunk in qa_service.chat_stream(
            query=request.query,
            knowledge_base_id=request.knowledge_base_id,
            chat_history=history,
            top_k=request.top_k or 10,
            min_score=request.min_score or 0.3,
            is_write_mode=True,
            max_context_chars=request.max_context_chars or MAX_CONTEXT_CHARS,
            use_rerank=request.use_rerank if request.use_rerank is not None else True,
            use_kg=request.use_kg if request.use_kg is not None else True,
            kg_weight=request.kg_weight or 0.3,
            answer_mode=request.answer_mode or "strict",
        ):
            yield _sse_encode(chunk)
            if request.conversation_id:
                if "<!--RAG_META" in chunk:
                    try:
                        import re
                        m = re.search(r'<!--RAG_META\s+([\s\S]*?)\s+RAG_META-->', chunk)
                        if m:
                            citations = json.loads(m.group(1)).get("citations", [])
                    except Exception:
                        pass
                elif "\x02THINK_END\x02" not in chunk and "<!--RAG_META" not in chunk and "\x01" not in chunk:
                    full_answer += chunk

        if request.conversation_id and full_answer.strip():
            conv_service.append_message(
                conversation_id=request.conversation_id,
                role="assistant",
                content=full_answer.strip(),
                reference=citations or None,
            )
            # 后台异步刷新摘要
            asyncio.ensure_future(
                qa_service.refresh_summary(request.conversation_id)
            )

    return StreamingResponse(generate(), media_type="text/event-stream")
