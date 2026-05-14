
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, AsyncGenerator

from config import config
from core.retriever import SearchService
from core.answer_modes import get_preset, DEFAULT_MODE
from utils.logger import logger
from services.conversation_service import ConversationService


MODEL_CONTEXT_LIMIT = 128_000
CONTEXT_SAFE_RATIO  = 0.95
CONTEXT_SAFE_LIMIT  = int(MODEL_CONTEXT_LIMIT * CONTEXT_SAFE_RATIO)
CHARS_PER_TOKEN     = 2
MAX_OUTPUT_TOKENS   = 4096
MAX_CONTEXT_CHARS   = 32000

# 记忆压缩配置
SUMMARY_TOKEN_THRESHOLD = 40_000  # 历史 token 超过此值时触发摘要生成（留足空间给检索+输出）
SUMMARY_MIN_MESSAGES    = 6       # 最少消息数才考虑摘要（避免短对话频繁触发）
RECENT_KEEP_COUNT       = 6       # 压缩时保留最近 N 条消息原文
SUMMARY_MAX_CHARS       = 1500    # 摘要最大字符数

TRUNCATION_NOTICE = "······ 由于大模型上下文窗口大小限制，回答已经被大模型截断。"

_SUMMARY_SYSTEM_PROMPT = """你是对话摘要助手。请将以下多轮对话压缩为一段简洁的摘要，保留关键信息：
- 用户提出的核心问题和意图
- 助手给出的关键结论和事实
- 对话中涉及的重要实体、数据、决策
摘要应控制在500字以内，使用第三人称描述，不要遗漏重要上下文。"""


_SYSTEM_PROMPT_DEFAULT = """你是知识库问答助手。请严格遵守以下规则：
1. 仅根据下方「检索结果」的内容回答用户问题，直接给出答案；
2. 禁止输出"根据检索结果""根据以上内容"等元描述，禁止解释你的回答来源或推理过程；
3. 禁止编造检索结果中不存在的信息；
4. 如果检索结果为空或与问题完全无关，仅输出：当前问题不在知识库范围内，无法为您解答；
5. 回答应简洁、准确、专业，直接陈述事实。"""


class QuestionAnswering:

    def __init__(self):
        self.search_service = SearchService()


    @staticmethod
    def _estimate_tokens(messages: List[Dict[str, str]]) -> int:
        total_chars = 0
        for m in messages:
            total_chars += len(m.get("content", "")) + len(m.get("role", "")) + 4
        return total_chars // CHARS_PER_TOKEN

    @staticmethod
    def _compress_history(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        system_msgs = [m for m in messages if m["role"] == "system"]
        non_system  = [m for m in messages if m["role"] != "system"]

        current_user = non_system[-1:]
        recent       = non_system[-5:-1]
        old          = non_system[:-5]

        if not old:
            return messages

        summary_lines = ["以下是更早对话的摘要（已压缩）："]
        for m in old:
            role_label = "用户" if m["role"] == "user" else "助手"
            snippet = m.get("content", "")[:150].replace("\n", " ")
            summary_lines.append(f"{role_label}：{snippet}")
        summary_msg = {
            "role": "user",
            "content": "\n".join(summary_lines),
        }

        compressed = system_msgs + [summary_msg] + recent + current_user
        logger.info(
            f"[Context] 历史压缩触发：旧历史 {len(old)} 条 → 1 条摘要，"
            f"保留最近 {len(recent)} 条 + 当前问题"
        )
        return compressed

    def _build_messages_with_context_guard(
        self,
        query: str,
        context: str,
        is_write_mode: bool = False,
        chat_history: List[Dict[str, str]] = None,
        system_suffix: str = "",
        system_prompt_override: str = "",
    ) -> List[Dict[str, str]]:
        if system_prompt_override:
            system_prompt = system_prompt_override
        else:
            system_prompt = _SYSTEM_PROMPT_DEFAULT
        if system_suffix:
            system_prompt = f"{system_prompt}\n\n{system_suffix}"
        messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]

        if chat_history:
            for h in chat_history:
                role = h.get("role", "user")
                if role in ("user", "assistant"):
                    messages.append({"role": role, "content": h.get("content", "")})

        user_content = f"检索结果：\n{context}\n\n用户问题：\n{query}"
        messages.append({"role": "user", "content": user_content})

        estimated = self._estimate_tokens(messages)
        logger.info(
            f"[Context] 估算 token={estimated} / 安全阈值={CONTEXT_SAFE_LIMIT} "
            f"（历史条数={len(chat_history) if chat_history else 0}，"
            f"检索内容={len(context)} 字符）"
        )

        if estimated > CONTEXT_SAFE_LIMIT:
            logger.warning(
                f"[Context] 估算 token={estimated} 超过安全阈值 {CONTEXT_SAFE_LIMIT}，"
                f"触发历史压缩"
            )
            messages = self._compress_history(messages)
            estimated_after = self._estimate_tokens(messages)
            logger.info(f"[Context] 压缩后估算 token={estimated_after}")

        return messages


    def _build_context(
        self,
        results: List[Dict[str, Any]],
        max_chars: int = MAX_CONTEXT_CHARS,
    ) -> str:
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

            meta_bits = [f"doc: {doc_id}", f"chunk: {chunk_idx}"]
            if page_idx:
                meta_bits.append(f"page: {page_idx}")
            if score:
                meta_bits.append(f"score: {score:.3f}")
            meta_line = ", ".join(meta_bits)

            parts.append(f"[段落 {i}] ({meta_line})\n{content}")
            total_chars += len(content)

        return "\n\n---\n\n".join(parts)


    async def chat(
        self,
        query: str,
        knowledge_base_id: str,
        chat_history: List[Dict[str, str]] = None,
        top_k: int = 10,
        min_score: float = 0.3,
        is_write_mode: bool = False,
        max_context_chars: int = MAX_CONTEXT_CHARS,
        use_rerank: bool = True,
        use_kg: bool = True,
        kg_weight: float = 0.3,
        answer_mode: str = DEFAULT_MODE,
    ) -> Dict[str, Any]:
        try:
            preset = get_preset(answer_mode)
            r = preset["retrieval"]
            logger.info(f"[QuestionAnswering] answer_mode={answer_mode}")

            results = self.search_service.search(
                query=query,
                knowledge_base_id=knowledge_base_id,
                top_k=r.get("top_k", top_k),
                min_score=r.get("min_score", min_score),
                use_rerank=r.get("use_rerank", use_rerank),
                use_kg=r.get("use_kg", use_kg),
                kg_weight=r.get("kg_weight", kg_weight),
                bm25_weight=r.get("bm25_weight", 1.0),
                vector_weight=r.get("vector_weight", 1.0),
            )

            context = self._build_context(results, max_context_chars)
            messages = self._build_messages_with_context_guard(
                query, context, is_write_mode, chat_history,
                system_suffix=preset.get("system_suffix", ""),
                system_prompt_override=preset.get("system_prompt_override", ""),
            )

            answer, finish_reason = await self._call_llm(messages, llm_overrides=preset["llm"])

            if finish_reason == "length":
                answer += TRUNCATION_NOTICE

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


    async def chat_stream(
        self,
        query: str,
        knowledge_base_id: str,
        chat_history: List[Dict[str, str]] = None,
        top_k: int = 10,
        min_score: float = 0.3,
        is_write_mode: bool = False,
        max_context_chars: int = MAX_CONTEXT_CHARS,
        use_rerank: bool = True,
        use_kg: bool = True,
        kg_weight: float = 0.3,
        answer_mode: str = DEFAULT_MODE,
    ) -> AsyncGenerator[str, None]:
        try:
            preset = get_preset(answer_mode)
            r = preset["retrieval"]
            logger.info(f"[QuestionAnswering] stream answer_mode={answer_mode}")

            results = self.search_service.search(
                query=query,
                knowledge_base_id=knowledge_base_id,
                top_k=r.get("top_k", top_k),
                min_score=r.get("min_score", min_score),
                use_rerank=r.get("use_rerank", use_rerank),
                use_kg=r.get("use_kg", use_kg),
                kg_weight=r.get("kg_weight", kg_weight),
                bm25_weight=r.get("bm25_weight", 1.0),
                vector_weight=r.get("vector_weight", 1.0),
            )

            context = self._build_context(results, max_context_chars)
            messages = self._build_messages_with_context_guard(
                query, context, is_write_mode, chat_history,
                system_suffix=preset.get("system_suffix", ""),
                system_prompt_override=preset.get("system_prompt_override", ""),
            )

            truncated = False
            async for chunk, finish_reason in self._call_llm_stream(messages, llm_overrides=preset["llm"]):
                yield chunk
                if finish_reason == "length":
                    truncated = True

            if truncated:
                yield TRUNCATION_NOTICE

            citations = self._extract_citations(results)
            meta = {
                "citations": citations,
                "search_results": results[:5],
                "timestamp": datetime.now().isoformat(),
            }
            yield "<!--RAG_META " + json.dumps(meta, ensure_ascii=False) + " RAG_META-->"

        except Exception as e:
            logger.error(f"[QuestionAnswering] 流式问答失败: {e}", exc_info=True)
            yield f"抱歉，处理您的请求时出现错误: {str(e)}"


    def _build_request_body(
        self,
        messages: List[Dict[str, str]],
        stream: bool,
        llm_overrides: Optional[Dict[str, Any]] = None,
    ) -> dict:
        o = llm_overrides or {}
        body: dict = {
            "model": config.llm.MODEL,
            "messages": messages,
            "stream": stream,
            "max_tokens": MAX_OUTPUT_TOKENS,
            "temperature": o.get("temperature", config.llm.TEMPERATURE),
            "top_p": o.get("top_p", config.llm.TOP_P),
        }
        freq_pen = o.get("frequency_penalty", config.llm.FREQUENCY_PENALTY)
        if freq_pen and freq_pen != 0:
            body["frequency_penalty"] = freq_pen
        return body

    async def _call_llm(
        self,
        messages: List[Dict[str, str]],
        llm_overrides: Optional[Dict[str, Any]] = None,
    ) -> tuple[str, str]:
        import httpx
        url = f"{config.llm.BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.llm.API_KEY}",
        }
        body = self._build_request_body(messages, stream=False, llm_overrides=llm_overrides)
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(url, headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()
                choice = data["choices"][0]
                finish_reason = choice.get("finish_reason", "")
                content = choice["message"]["content"] or ""
                return content, finish_reason
        except Exception as e:
            logger.error(f"[QuestionAnswering] LLM 调用失败: {e}")
            return "抱歉，生成回答时出现错误。", ""

    async def _call_llm_stream(
        self,
        messages: List[Dict[str, str]],
        llm_overrides: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[tuple[str, str], None]:
        import httpx
        url = f"{config.llm.BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.llm.API_KEY}",
            "Accept": "text/event-stream",
        }
        body = self._build_request_body(messages, stream=True, llm_overrides=llm_overrides)
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
                                yield "\x02THINK_END\x02", ""
                                thinking_ended = True
                            break
                        try:
                            import json as _json
                            chunk = _json.loads(data_str)
                            choice = chunk["choices"][0]
                            delta = choice.get("delta", {})
                            finish_reason = choice.get("finish_reason") or ""
                            reasoning = delta.get("reasoning_content") or ""
                            content = delta.get("content") or ""

                            if reasoning:
                                import base64 as _b64
                                encoded = _b64.b64encode(reasoning.encode()).decode()
                                yield f"\x01{encoded}\x01", ""

                            if content:
                                if not thinking_ended:
                                    yield "\x02THINK_END\x02", ""
                                    thinking_ended = True
                                yield content, finish_reason
                            elif finish_reason:
                                yield "", finish_reason
                        except Exception:
                            continue
        except Exception as e:
            logger.error(f"[QuestionAnswering] LLM 流式调用失败: {e}")
            yield f"抱歉，生成回答时出现错误：{str(e)}", ""


    # ─── 记忆压缩升级：LLM 摘要 ─────────────────────────────────

    async def _summarize_with_llm(
        self,
        messages_to_summarize: List[Dict[str, str]],
    ) -> str:
        """调用 LLM 将多轮对话压缩为语义摘要"""
        if not messages_to_summarize:
            return ""

        # 构造待摘要的对话文本
        dialogue_lines = []
        for m in messages_to_summarize:
            role_label = "用户" if m["role"] == "user" else "助手"
            # 每条消息截取前 800 字，避免摘要输入过长
            content = m.get("content", "")[:800]
            dialogue_lines.append(f"{role_label}：{content}")

        dialogue_text = "\n".join(dialogue_lines)
        # 限制总输入长度
        if len(dialogue_text) > 8000:
            dialogue_text = dialogue_text[:8000] + "\n…（后续对话已省略）"

        summary_messages = [
            {"role": "system", "content": _SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": f"请对以下对话生成摘要：\n\n{dialogue_text}"},
        ]

        try:
            import httpx
            url = f"{config.llm.BASE_URL.rstrip('/')}/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config.llm.API_KEY}",
            }
            body = {
                "model": config.llm.MODEL,
                "messages": summary_messages,
                "stream": False,
                "max_tokens": 800,
                "temperature": 0.3,
                "top_p": 0.7,
            }
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(url, headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()
                summary = data["choices"][0]["message"]["content"] or ""
                # 截断过长摘要
                if len(summary) > SUMMARY_MAX_CHARS:
                    summary = summary[:SUMMARY_MAX_CHARS] + "…"
                logger.info(f"[Memory] LLM 摘要生成完成，长度={len(summary)}")
                return summary
        except Exception as e:
            logger.error(f"[Memory] LLM 摘要生成失败: {e}")
            return ""

    async def refresh_summary(self, conversation_id: str) -> None:
        """
        后台刷新会话摘要。在每次回答完成后异步调用。
        触发策略：基于 token 估算 —— 当历史消息总 token 超过 SUMMARY_TOKEN_THRESHOLD 时，
        对较早的消息生成 LLM 摘要并缓存到 DB。同时要求最少 SUMMARY_MIN_MESSAGES 条消息。
        """
        conv_service = ConversationService()
        try:
            # 获取所有消息
            all_msgs = conv_service.get_messages(conversation_id)
            if not all_msgs or len(all_msgs) <= SUMMARY_MIN_MESSAGES:
                return  # 消息太少，无需摘要

            # 估算全部历史的 token 量
            history_for_estimate = [
                {"role": m["role"], "content": m["content"]}
                for m in all_msgs
            ]
            total_tokens = self._estimate_tokens(history_for_estimate)

            if total_tokens <= SUMMARY_TOKEN_THRESHOLD:
                return  # token 量未达阈值，无需压缩

            logger.info(
                f"[Memory] 历史 token={total_tokens} 超过阈值 {SUMMARY_TOKEN_THRESHOLD}，"
                f"触发摘要生成 (消息数={len(all_msgs)})"
            )

            # 确定需要摘要的范围：保留最近 RECENT_KEEP_COUNT 条，其余生成摘要
            if len(all_msgs) <= RECENT_KEEP_COUNT:
                return

            msgs_to_summarize = all_msgs[:-RECENT_KEEP_COUNT]
            last_summarized_id = msgs_to_summarize[-1]["id"]

            # 检查是否已有覆盖到此 ID 的摘要
            existing = conv_service.get_summary(conversation_id)
            if existing and existing.get("summary_up_to") and existing["summary_up_to"] >= last_summarized_id:
                return  # 摘要已是最新

            # 如果已有旧摘要，将旧摘要作为前缀 + 新增消息一起摘要（增量压缩）
            old_summary = existing["summary"] if existing else ""
            if old_summary and existing.get("summary_up_to"):
                # 只摘要旧摘要覆盖之后、新截断点之前的消息
                new_msgs = [
                    {"role": m["role"], "content": m["content"]}
                    for m in msgs_to_summarize
                    if m["id"] > existing["summary_up_to"]
                ]
                if not new_msgs:
                    return
                # 将旧摘要 + 新消息一起送入 LLM 做增量摘要
                incremental_input = [
                    {"role": "assistant", "content": f"[之前的对话摘要] {old_summary}"}
                ] + new_msgs
                summary = await self._summarize_with_llm(incremental_input)
            else:
                # 首次生成摘要
                plain_msgs = [
                    {"role": m["role"], "content": m["content"]}
                    for m in msgs_to_summarize
                ]
                summary = await self._summarize_with_llm(plain_msgs)

            if summary:
                conv_service.update_summary(conversation_id, summary, last_summarized_id)
                logger.info(
                    f"[Memory] 摘要已缓存 conv_id={conversation_id} "
                    f"压缩前 token≈{total_tokens} → 摘要 {len(summary)} 字符"
                )

        except Exception as e:
            logger.error(f"[Memory] 刷新摘要失败 conv_id={conversation_id}: {e}")

    def prepare_history_with_memory(
        self,
        conversation_id: str,
    ) -> List[Dict[str, str]]:
        """
        智能加载对话历史：优先使用缓存摘要 + 近期消息，减少 token 消耗。
        返回适合传给 _build_messages_with_context_guard 的 chat_history 列表。
        """
        conv_service = ConversationService()

        # 检查是否有缓存摘要
        cached = conv_service.get_summary(conversation_id)
        if cached and cached.get("summary"):
            # 使用摘要 + 摘要之后的消息
            recent_msgs = conv_service.get_messages_after(
                conversation_id, cached["summary_up_to"]
            )
            # 构造：摘要作为一条 system-like 上下文 + 近期原文
            history = [
                {"role": "assistant", "content": f"[对话历史摘要] {cached['summary']}"}
            ] + recent_msgs
            logger.info(
                f"[Memory] 使用缓存摘要 + {len(recent_msgs)} 条近期消息 "
                f"(摘要覆盖到 msg_id={cached['summary_up_to']})"
            )
            return history
        else:
            # 无缓存摘要，返回全部历史（由 _compress_history 兜底）
            return conv_service.get_messages_for_llm(conversation_id)

    def _extract_citations(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        citations = []
        seen = set()
        for doc in results:
            chunk_id = doc.get("chunk_id", "")
            doc_id = doc.get("doc_id", "")
            key = chunk_id or f"{doc_id}_{len(citations)}"
            if key in seen:
                continue
            seen.add(key)

            content = doc.get("content", "")
            score = (
                doc.get("rerank_score")
                or doc.get("rrf_score")
                or doc.get("similarity")
                or 0
            )
            citations.append({
                "doc_id": doc_id,
                "chunk_id": chunk_id,
                "docnm_kwd": doc.get("docnm_kwd", ""),
                "page_num_int": doc.get("page_num_int", []),
                "content_preview": content[:300] + "…" if len(content) > 300 else content,
                "score": score,
            })
            if len(citations) >= 5:
                break
        return citations
