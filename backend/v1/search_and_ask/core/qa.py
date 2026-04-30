"""
核心模块：问答生成器

基于检索结果构建 prompt，调用 LLM 生成回答。
支持标准模式 / 撰写模式，以及流式 / 非流式两种输出。
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional, AsyncGenerator

from config import config
from core.retriever import SearchService
from utils.logger import logger


# ---------------------------------------------------------------------------
# Prompt 模板
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT_QA = """你是基于知识库检索的RAG问答助手，必须严格遵守以下规则：
1. 仅依据检索到的知识库内容回答用户问题；
2. 若用户输入为打招呼、闲聊、无意义语句、与知识库内容完全不相关的问题，**统一固定输出：当前问题不在知识库范围内，无法为您解答**
3. 禁止编造知识库以外的内容，禁止随意闲聊、回答无关常识问题；
4. 不解释理由、不额外多说废话，命中无关场景直接输出指定固定文案即可。"""

_SYSTEM_PROMPT_WRITE = """你是基于知识库检索的RAG问答助手，必须严格遵守以下规则：
1. 仅依据检索到的知识库内容回答用户问题；
2. 若用户输入为打招呼、闲聊、无意义语句、与知识库内容完全不相关的问题，**统一固定输出：当前问题不在知识库范围内，无法为您解答**
3. 禁止编造知识库以外的内容，禁止随意闲聊、回答无关常识问题；
4. 不解释理由、不额外多说废话，命中无关场景直接输出指定固定文案即可。"""


class QuestionAnswering:
    """问答生成器"""

    def __init__(self):
        self.search_service = SearchService()

    # ==================================================================
    # 上下文构建
    # ==================================================================

    def _build_context(
        self,
        results: List[Dict[str, Any]],
        max_chars: int = 8000,
    ) -> str:
        """从检索结果构建 LLM 上下文，适配父子检索模式的父块输出"""
        if not results:
            return "（无相关检索结果）"

        parts = []
        total_chars = 0

        for i, doc in enumerate(results, 1):
            content = doc.get("content", "")
            if not content:
                continue

            if total_chars + len(content) > max_chars:
                remaining = max_chars - total_chars
                if remaining > 200:
                    content = content[:remaining] + "…"
                else:
                    break

            doc_id = doc.get("doc_id", "unknown")
            chunk_idx = doc.get("chunk_index", 0)
            page_idx = doc.get("page_idx", 0)
            score = doc.get("score") or doc.get("avg_score") or doc.get("similarity", 0)
            child_count = doc.get("child_count", 0)

            meta_bits = [f"doc: {doc_id}", f"chunk: {chunk_idx}"]
            if page_idx:
                meta_bits.append(f"page: {page_idx}")
            if score:
                meta_bits.append(f"score: {score:.3f}")
            if child_count:
                meta_bits.append(f"命中子块: {child_count}")
            meta_line = ", ".join(meta_bits)

            parts.append(f"[段落 {i}] ({meta_line})\n{content}")
            total_chars += len(content)

        return "\n\n---\n\n".join(parts)

    def _build_prompt(
        self,
        query: str,
        context: str,
        is_write_mode: bool = False,
        chat_history: List[Dict[str, str]] = None,
    ) -> str:
        """构建完整 prompt（含对话历史）"""
        history_text = ""
        if chat_history:
            recent = chat_history[-6:]
            lines = []
            for h in recent:
                role = "用户" if h.get("role") == "user" else "助手"
                lines.append(f"{role}: {h.get('content', '')}")
            history_text = "对话历史：\n" + "\n".join(lines) + "\n\n"

        return f"""{history_text}检索结果：
{context}

用户问题：
{query}

请回答："""

    def _build_messages(
        self,
        query: str,
        context: str,
        is_write_mode: bool = False,
        chat_history: List[Dict[str, str]] = None,
    ) -> List[Dict[str, str]]:
        """构建 OpenAI messages 列表"""
        system = _SYSTEM_PROMPT_WRITE if is_write_mode else _SYSTEM_PROMPT_QA
        messages = [{"role": "system", "content": system}]

        if chat_history:
            for h in chat_history[-6:]:
                role = h.get("role", "user")
                if role in ("user", "assistant"):
                    messages.append({"role": role, "content": h.get("content", "")})

        user_content = f"检索结果：\n{context}\n\n用户问题：\n{query}"
        messages.append({"role": "user", "content": user_content})
        return messages

    # ==================================================================
    # 非流式问答
    # ==================================================================

    async def chat(
        self,
        query: str,
        knowledge_base_id: str,
        chat_history: List[Dict[str, str]] = None,
        top_k: int = 10,
        min_score: float = 0.3,
        is_write_mode: bool = False,
        max_context_chars: int = 8000,
        use_rerank: bool = True,
        use_kg: bool = True,
        kg_weight: float = 0.3,
    ) -> Dict[str, Any]:
        """标准问答（非流式），返回 {"answer", "citations", "search_results", "timestamp"}"""
        try:
            results = self.search_service.search(
                query=query,
                knowledge_base_id=knowledge_base_id,
                top_k=top_k,
                min_score=min_score,
                use_rerank=use_rerank,
                fetch_parents=True,
                use_kg=use_kg,
                kg_weight=kg_weight,
            )

            context = self._build_context(results, max_context_chars)
            messages = self._build_messages(query, context, is_write_mode, chat_history)

            answer = await self._call_llm(messages)
            citations = self._extract_citations(results)

            return {
                "answer": answer,
                "citations": citations,
                "search_results": results[:5],
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"[QuestionAnswering] 问答失败: {e}", exc_info=True)
            return {
                "answer": f"抱歉，处理您的请求时出现错误: {str(e)}",
                "citations": [],
                "search_results": [],
                "timestamp": datetime.now().isoformat(),
            }

    # ==================================================================
    # 流式问答
    # ==================================================================

    async def chat_stream(
        self,
        query: str,
        knowledge_base_id: str,
        chat_history: List[Dict[str, str]] = None,
        top_k: int = 10,
        min_score: float = 0.3,
        is_write_mode: bool = False,
        max_context_chars: int = 8000,
        use_rerank: bool = True,
        use_kg: bool = True,
        kg_weight: float = 0.3,
    ) -> AsyncGenerator[str, None]:
        """流式问答，末尾附 RAG_META 元数据"""
        try:
            results = self.search_service.search(
                query=query,
                knowledge_base_id=knowledge_base_id,
                top_k=top_k,
                min_score=min_score,
                use_rerank=use_rerank,
                fetch_parents=True,
                use_kg=use_kg,
                kg_weight=kg_weight,
            )

            context = self._build_context(results, max_context_chars)
            messages = self._build_messages(query, context, is_write_mode, chat_history)

            async for chunk in self._call_llm_stream(messages):
                yield chunk

            citations = self._extract_citations(results)
            meta = {
                "citations": citations,
                "search_results": results[:5],
                "timestamp": datetime.now().isoformat(),
            }
            yield "\n\n<!--RAG_META " + json.dumps(meta, ensure_ascii=False) + " RAG_META-->"

        except Exception as e:
            logger.error(f"[QuestionAnswering] 流式问答失败: {e}", exc_info=True)
            yield f"\n\n抱歉，处理您的请求时出现错误: {str(e)}"

    # ==================================================================
    # LLM 调用（使用 AsyncOpenAI）
    # ==================================================================

    def _build_request_body(self, messages: List[Dict[str, str]], stream: bool) -> dict:
        """构建符合 Gitee AI 规范的请求体"""
        body: dict = {
            "model": config.llm.MODEL,
            "messages": messages,
            "stream": stream,
            "max_tokens": config.llm.MAX_TOKENS,
            # 降低随机性，让模型严格遵守 system prompt 指令
            "temperature": 0.1,
            "top_p": 0.8,
            "n": 1,
            # 开启 Qwen3 思考链，reasoning_content 由前端单独渲染
            "enable_thinking": True,
        }
        # frequency_penalty 仅在非零时传入，避免部分模型（如 DeepSeek）因该字段返回 400
        if config.llm.FREQUENCY_PENALTY != 0:
            body["frequency_penalty"] = config.llm.FREQUENCY_PENALTY
        return body

    async def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """调用 LLM（非流式，httpx 直接请求）"""
        import httpx
        url = f"{config.llm.BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.llm.API_KEY}",
        }
        body = self._build_request_body(messages, stream=False)
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(url, headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"] or ""
        except Exception as e:
            logger.error(f"[QuestionAnswering] LLM 调用失败: {e}")
            return "抱歉，生成回答时出现错误。"

    async def _call_llm_stream(
        self, messages: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """调用 LLM（流式，httpx 直接请求 SSE）"""
        import httpx
        url = f"{config.llm.BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.llm.API_KEY}",
            "Accept": "text/event-stream",
        }
        body = self._build_request_body(messages, stream=True)
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream("POST", url, headers=headers, json=body) as resp:
                    if resp.status_code != 200:
                        err = await resp.aread()
                        raise RuntimeError(f"HTTP {resp.status_code}: {err.decode(errors='replace')}")
                    thinking_ended = False
                    async for line in resp.aiter_lines():
                        line = line.strip()
                        if not line or not line.startswith("data: "):
                            continue
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            if not thinking_ended:
                                # 通知思考结束（路由层会统一加 data: 前缀）
                                yield "\x02THINK_END\x02"
                                thinking_ended = True
                            break
                        try:
                            import json as _json
                            chunk = _json.loads(data_str)
                            delta = chunk["choices"][0].get("delta", {})
                            reasoning = delta.get("reasoning_content") or ""
                            content = delta.get("content") or ""

                            # 思考链内容：用 \x01 包裹（不会出现在正文中），前端单独渲染
                            if reasoning:
                                # 对 reasoning 内容做 base64 编码，避免换行破坏 SSE 格式
                                import base64 as _b64
                                encoded = _b64.b64encode(reasoning.encode()).decode()
                                yield f"\x01{encoded}\x01"

                            # 正式回答内容：思考链结束时先发结束标记
                            if content:
                                if not thinking_ended:
                                    yield "\x02THINK_END\x02"
                                    thinking_ended = True
                                yield content
                        except Exception:
                            continue
        except Exception as e:
            logger.error(f"[QuestionAnswering] LLM 流式调用失败: {e}")
            yield f"\n\n抱歉，生成回答时出现错误：{str(e)}"

    # ==================================================================
    # 引用
    # ==================================================================

    def _extract_citations(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从检索结果提取前 5 条去重引用"""
        citations = []
        seen = set()
        for doc in results:
            doc_id = doc.get("doc_id", "")
            chunk_idx = doc.get("chunk_index", 0)
            key = (doc_id, chunk_idx)
            if key in seen:
                continue
            seen.add(key)
            content = doc.get("content", "")
            citations.append({
                "doc_id": doc_id,
                "chunk_index": chunk_idx,
                "page_idx": doc.get("page_idx", 0),
                "content_preview": content[:200] + "…" if len(content) > 200 else content,
                "score": doc.get("score") or doc.get("avg_score") or 0,
            })
        return citations[:5]
