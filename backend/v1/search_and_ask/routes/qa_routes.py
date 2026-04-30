"""
问答路由 — 检索 + LLM 生成回答（流式 / 非流式 / 撰写模式）

对话持久化说明：
- 新增 /conversation/* 接口管理会话（创建、列表、删除）
- /ask/stream 和 /writechat/stream 支持 conversation_id 参数
  - 传入 conversation_id：从数据库加载历史，回答后自动保存
  - 不传：退回原有 chat_history 参数模式（兼容旧调用）
- 历史截断统一由后端 qa.py 的 token 估算 + 动态压缩机制负责
"""

import json
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from models.schemas import ChatRequest
from core.qa import QuestionAnswering, MAX_CONTEXT_CHARS
from services.conversation_service import ConversationService
from utils.logger import logger


def _sse_encode(chunk: str) -> str:
    """
    将一个 chunk 编码为合法的 SSE 事件。

    SSE 规范要求每行以 'data: ' 开头，多行内容需拆分为多个 data 行。
    如果 chunk 包含换行符而不拆分，前端解析器会丢失换行后的内容。
    """
    if '\n' not in chunk:
        return f"data: {chunk}\n\n"
    # 多行内容：每行单独加 data: 前缀，最后空行结束事件
    lines = chunk.split('\n')
    return ''.join(f"data: {line}\n" for line in lines) + "\n"

router = APIRouter(tags=["问答"])
qa_service = QuestionAnswering()
conv_service = ConversationService()


# ---------------------------------------------------------------------------
# 对话管理接口
# ---------------------------------------------------------------------------

class CreateConversationRequest(BaseModel):
    user_id: str                        # 用户ID，管理员传 "admin"
    kb_id: str                          # 关联知识库ID
    title: Optional[str] = "新对话"


class UpdateTitleRequest(BaseModel):
    title: str


@router.post("/conversation/create")
async def create_conversation(req: CreateConversationRequest):
    """创建新会话，返回 conversation_id"""
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
    """获取用户的会话列表"""
    result = conv_service.list_by_user(user_id=user_id, page=page, size=size)
    return {"code": 200, "data": result}


@router.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """获取会话详情 + 完整消息列表"""
    conv = conv_service.get(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    messages = conv_service.get_messages(conversation_id)
    return {"code": 200, "data": {**conv, "messages": messages}}


@router.delete("/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """删除会话（级联删除消息）"""
    ok = conv_service.delete(conversation_id)
    if not ok:
        raise HTTPException(status_code=404, detail="会话不存在或删除失败")
    return {"code": 200, "message": "删除成功"}


@router.put("/conversation/{conversation_id}/title")
async def update_conversation_title(conversation_id: str, req: UpdateTitleRequest):
    """更新会话标题"""
    ok = conv_service.update_title(conversation_id, req.title)
    return {"code": 200 if ok else 404, "message": "更新成功" if ok else "会话不存在"}


# ---------------------------------------------------------------------------
# 非流式问答（兼容旧接口，不涉及 conversation_id）
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
            max_context_chars=request.max_context_chars or MAX_CONTEXT_CHARS,
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
# 流式问答（核心接口，支持 conversation_id 持久化）
# ---------------------------------------------------------------------------

class StreamAskRequest(BaseModel):
    """流式问答请求（扩展版，支持 conversation_id）"""
    query: str
    knowledge_base_id: str
    conversation_id: Optional[str] = None      # 传入则从数据库加载历史并保存
    chat_history: Optional[list] = None        # 兼容旧模式（不传 conversation_id 时使用）
    top_k: Optional[int] = 10
    min_score: Optional[float] = 0.3
    is_write_mode: Optional[bool] = False
    max_context_chars: Optional[int] = None
    use_rerank: Optional[bool] = True
    use_kg: Optional[bool] = True
    kg_weight: Optional[float] = 0.3


@router.post("/ask/stream")
async def ask_stream_endpoint(request: StreamAskRequest):
    """
    标准问答（SSE 流式）

    两种模式：
    1. 传 conversation_id：从数据库加载历史 → 问答 → 自动保存消息
    2. 不传（兼容旧模式）：使用 chat_history 参数
    """
    async def generate():
        # ── 加载历史 ──────────────────────────────────────────────────
        if request.conversation_id:
            history = conv_service.get_messages_for_llm(request.conversation_id)
            logger.info(
                f"[AskStream] conv_id={request.conversation_id} "
                f"加载历史 {len(history)} 条"
            )
        else:
            history = request.chat_history or []

        # ── 先保存用户消息 ─────────────────────────────────────────────
        if request.conversation_id:
            conv_service.append_message(
                conversation_id=request.conversation_id,
                role="user",
                content=request.query,
            )
            # 如果是第一条用户消息，自动更新会话标题
            conv = conv_service.get(request.conversation_id)
            if conv and conv.get("title") == "新对话":
                conv_service.update_title(
                    request.conversation_id,
                    request.query[:40],
                )

        # ── 流式生成 ──────────────────────────────────────────────────
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
        ):
            yield _sse_encode(chunk)

            # 收集完整回答内容（用于保存到数据库）
            if request.conversation_id:
                # 解析 RAG_META 提取 citations
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
                    # 思考链 base64 内容，解码后累积
                    import re, base64
                    for b64 in re.findall(r'\x01([A-Za-z0-9+/=]+)\x01', chunk):
                        try:
                            full_thinking += base64.b64decode(b64).decode("utf-8")
                        except Exception:
                            pass
                elif "\x02THINK_END\x02" not in chunk and "<!--RAG_META" not in chunk:
                    full_answer += chunk

        # ── 保存 assistant 消息到数据库 ───────────────────────────────
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
            max_context_chars=request.max_context_chars or MAX_CONTEXT_CHARS,
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
async def writechat_stream_endpoint(request: StreamAskRequest):
    """撰写模式（SSE 流式），同样支持 conversation_id"""
    async def generate():
        if request.conversation_id:
            history = conv_service.get_messages_for_llm(request.conversation_id)
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

    return StreamingResponse(generate(), media_type="text/event-stream")
