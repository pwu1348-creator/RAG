"""
核心模块：问答生成器

基于检索结果构建 prompt，调用 LLM 生成回答。
支持标准模式 / 撰写模式，以及流式 / 非流式两种输出。

上下文管理策略（适配 Qwen3-235B-A22B 128K 窗口）：
- 统一由后端管控历史长度，前端/接口层不再截断
- 用 2字符≈1token 快速估算，总输入不超过 121600 token（128K×95%）
- 超阈值时自动压缩旧历史：保留 system + 最近2轮，其余合并为摘要
- 检索内容上限放开到 32000 字符，LLM 输出上限 4096 token
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional, AsyncGenerator

from config import config
from core.retriever import SearchService
from core.answer_modes import get_preset, DEFAULT_MODE
from utils.logger import logger
from services.conversation_service import ConversationService


# ---------------------------------------------------------------------------
# 上下文窗口常量
# ---------------------------------------------------------------------------

MODEL_CONTEXT_LIMIT = 128_000   # Qwen3-235B-A22B 上下文窗口（token）
CONTEXT_SAFE_RATIO  = 0.95      # 安全阈值 95%
CONTEXT_SAFE_LIMIT  = int(MODEL_CONTEXT_LIMIT * CONTEXT_SAFE_RATIO)  # 121600
CHARS_PER_TOKEN     = 2         # 中英混合粗估：2字符 ≈ 1 token
MAX_OUTPUT_TOKENS   = 4096      # LLM 单次输出上限（原2048，现放开到4096）
MAX_CONTEXT_CHARS   = 32000     # 检索内容最大字符（原8000，现放开到32000）

# 截断提示（finish_reason=length 时追加）
# 注意：不能以 \n\n 开头，否则会破坏 SSE data: 格式
TRUNCATION_NOTICE = "······ 由于大模型上下文窗口大小限制，回答已经被大模型截断。"


# ---------------------------------------------------------------------------
# Prompt 模板
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT_QA = """你是知识库问答助手。请严格遵守以下规则：
1. 仅根据下方「检索结果」的内容回答用户问题，直接给出答案；
2. 禁止输出"根据检索结果""根据以上内容"等元描述，禁止解释你的回答来源或推理过程；
3. 禁止编造检索结果中不存在的信息；
4. 如果检索结果为空或与问题完全无关，仅输出：当前问题不在知识库范围内，无法为您解答；
5. 回答应简洁、准确、专业，直接陈述事实。"""

_SYSTEM_PROMPT_WRITE = """你是知识库问答助手。请严格遵守以下规则：
1. 仅根据下方「检索结果」的内容回答用户问题，直接给出答案；
2. 禁止输出"根据检索结果""根据以上内容"等元描述，禁止解释你的回答来源或推理过程；
3. 禁止编造检索结果中不存在的信息；
4. 如果检索结果为空或与问题完全无关，仅输出：当前问题不在知识库范围内，无法为您解答；
5. 以专业、详细的方式组织回答，适当使用标题、列表等 Markdown 格式，直接陈述内容。"""


class QuestionAnswering:
    """问答生成器"""

    def __init__(self):
        self.search_service = SearchService()

    # ==================================================================
    # ── Token 估算 & 历史压缩工具方法 ──────────────────────────────────
    # ==================================================================

    @staticmethod
    def _estimate_tokens(messages: List[Dict[str, str]]) -> int:
        """
        快速估算 messages 列表的 token 占用。
        中英混合按 2字符≈1token 计算，包含 role 字段开销。
        """
        total_chars = 0
        for m in messages:
            # role 本身也占 token，加固定开销 4
            total_chars += len(m.get("content", "")) + len(m.get("role", "")) + 4
        return total_chars // CHARS_PER_TOKEN

    @staticmethod
    def _compress_history(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        历史压缩：超过安全阈值时调用。
        策略：保留 system + 最近2轮（4条消息），把更早的历史合并为一条摘要。
        """
        system_msgs = [m for m in messages if m["role"] == "system"]
        non_system  = [m for m in messages if m["role"] != "system"]

        # 最后一条是当前用户问题（含检索结果），倒数2-5条是最近2轮历史
        # 结构：[...old_history..., recent_4_msgs, current_user_msg]
        current_user = non_system[-1:]          # 当前问题（最后1条）
        recent       = non_system[-5:-1]        # 最近2轮（倒数2~5条，最多4条）
        old          = non_system[:-5]          # 更早的历史

        if not old:
            # 没有可压缩的旧历史，直接返回原始 messages
            return messages

        # 把旧历史拼成摘要（每条截取前150字，避免摘要本身过长）
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
    ) -> List[Dict[str, str]]:
        """
        构建 OpenAI messages 列表，并执行上下文安全检查。

        流程：
        1. 拼接 system + 完整历史 + 当前用户问题（含检索结果）
        2. 估算总 token
        3. 若超过 CONTEXT_SAFE_LIMIT，触发历史压缩
        4. 压缩后再次估算并记录日志

        system_suffix: 来自 answer_mode preset 的风格约束，拼到 system prompt 末尾。
        """
        system_prompt = _SYSTEM_PROMPT_WRITE if is_write_mode else _SYSTEM_PROMPT_QA
        if system_suffix:
            system_prompt = f"{system_prompt}\n\n{system_suffix}"
        messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]

        # 加入完整历史（不在此处截断，由后端统一管控）
        if chat_history:
            for h in chat_history:
                role = h.get("role", "user")
                if role in ("user", "assistant"):
                    messages.append({"role": role, "content": h.get("content", "")})

        # 当前用户问题（含检索结果）
        user_content = f"检索结果：\n{context}\n\n用户问题：\n{query}"
        messages.append({"role": "user", "content": user_content})

        # ── Token 估算 ──────────────────────────────────────────────────
        estimated = self._estimate_tokens(messages)
        logger.info(
            f"[Context] 估算 token={estimated} / 安全阈值={CONTEXT_SAFE_LIMIT} "
            f"（历史条数={len(chat_history) if chat_history else 0}，"
            f"检索内容={len(context)} 字符）"
        )

        # ── 超阈值时压缩 ────────────────────────────────────────────────
        if estimated > CONTEXT_SAFE_LIMIT:
            logger.warning(
                f"[Context] 估算 token={estimated} 超过安全阈值 {CONTEXT_SAFE_LIMIT}，"
                f"触发历史压缩"
            )
            messages = self._compress_history(messages)
            estimated_after = self._estimate_tokens(messages)
            logger.info(f"[Context] 压缩后估算 token={estimated_after}")

        return messages

    # ==================================================================
    # 上下文构建（检索结果 → 文本）
    # ==================================================================

    def _build_context(
        self,
        results: List[Dict[str, Any]],
        max_chars: int = MAX_CONTEXT_CHARS,
    ) -> str:
        """从检索结果构建 LLM 上下文"""
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
        max_context_chars: int = MAX_CONTEXT_CHARS,
        use_rerank: bool = True,
        use_kg: bool = True,
        kg_weight: float = 0.3,
        answer_mode: str = DEFAULT_MODE,
    ) -> Dict[str, Any]:
        """标准问答（非流式），返回 {"answer", "citations", "search_results", "timestamp"}"""
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
            )

            answer, finish_reason = await self._call_llm(messages, llm_overrides=preset["llm"])

            # 超限截断提示
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
        max_context_chars: int = MAX_CONTEXT_CHARS,
        use_rerank: bool = True,
        use_kg: bool = True,
        kg_weight: float = 0.3,
        answer_mode: str = DEFAULT_MODE,
    ) -> AsyncGenerator[str, None]:
        """流式问答，末尾附 RAG_META 元数据"""
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
            )

            truncated = False
            async for chunk, finish_reason in self._call_llm_stream(messages, llm_overrides=preset["llm"]):
                yield chunk
                if finish_reason == "length":
                    truncated = True

            # 超限截断提示（流式末尾追加）
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

    # ==================================================================
    # LLM 调用（使用 AsyncOpenAI）
    # ==================================================================

    def _build_request_body(
        self,
        messages: List[Dict[str, str]],
        stream: bool,
        llm_overrides: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """
        构建符合 Gitee AI 规范的请求体

        llm_overrides 优先级高于 config.llm 默认值；支持键：
        temperature / top_p / top_k / frequency_penalty / enable_thinking。
        """
        o = llm_overrides or {}
        body: dict = {
            "model": config.llm.MODEL,
            "messages": messages,
            "stream": stream,
            "max_tokens": MAX_OUTPUT_TOKENS,
            "temperature": o.get("temperature", config.llm.TEMPERATURE),
            "top_p": o.get("top_p", config.llm.TOP_P),
            "n": 1,
            "enable_thinking": o.get("enable_thinking", True),
        }
        # top_k 通过 body 顶层传入（Gitee OpenAI 兼容层透传给 Qwen）
        top_k_val = o.get("top_k", config.llm.TOP_K)
        if top_k_val and top_k_val > 0:
            body["top_k"] = top_k_val
        # frequency_penalty：enable_thinking 模式下部分模型不支持，跳过
        if not body.get("enable_thinking"):
            freq_pen = o.get("frequency_penalty", config.llm.FREQUENCY_PENALTY)
            if freq_pen and freq_pen != 0:
                body["frequency_penalty"] = freq_pen
        return body

    async def _call_llm(
        self,
        messages: List[Dict[str, str]],
        llm_overrides: Optional[Dict[str, Any]] = None,
    ) -> tuple[str, str]:
        """
        调用 LLM（非流式，httpx 直接请求）
        返回 (answer_text, finish_reason)
        """
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
        """
        调用 LLM（流式，httpx 直接请求 SSE）
        每次 yield (chunk_text, finish_reason)
        finish_reason 仅在最后一个 chunk 时非空
        """
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

                            # 思考链内容：用 \x01 包裹，前端单独渲染
                            if reasoning:
                                import base64 as _b64
                                encoded = _b64.b64encode(reasoning.encode()).decode()
                                yield f"\x01{encoded}\x01", ""

                            # 正式回答内容
                            if content:
                                if not thinking_ended:
                                    yield "\x02THINK_END\x02", ""
                                    thinking_ended = True
                                yield content, finish_reason
                            elif finish_reason:
                                # 无内容但有 finish_reason（如 length）
                                yield "", finish_reason
                        except Exception:
                            continue
        except Exception as e:
            logger.error(f"[QuestionAnswering] LLM 流式调用失败: {e}")
            yield f"抱歉，生成回答时出现错误：{str(e)}", ""

    # ==================================================================
    # 引用
    # ==================================================================

    def _extract_citations(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        从检索结果提取前 5 条去重引用。
        结果已按评分排序（rerank_score > rrf_score > similarity），
        直接按顺序取前 5 条不重复的 chunk。
        """
        citations = []
        seen = set()
        for doc in results:
            chunk_id = doc.get("chunk_id", "")
            doc_id = doc.get("doc_id", "")
            # 用 chunk_id 去重（每个 chunk 唯一）
            key = chunk_id or f"{doc_id}_{len(citations)}"
            if key in seen:
                continue
            seen.add(key)

            content = doc.get("content", "")
            # 取实际存在的评分字段
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
