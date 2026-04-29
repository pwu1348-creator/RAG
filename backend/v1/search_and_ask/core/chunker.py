"""
核心模块：父子分块器

将文档文本切分为父子两层结构：
- 父块 (parent)：章节/段落级，600~1200 tokens，保留完整语义上下文
- 子块 (child) ：200~350 tokens，嵌入父块之中，用于精确检索

子块绝不跨越父块边界，确保每个子块可通过 parent_chunk_id 回退完整父块。
"""

import re
import uuid
from typing import List, Dict, Any, Tuple

from utils.rag_tokenizer import RagTokenizer
from utils.logger import logger


class ParentChildChunker:
    """
    父子分块器

    工作流程：
    1. 按自然段落/标题将文本切分为 sections
    2. 将 sections 合并为 parent chunks（600-1200 tokens）
    3. 在每个 parent 内部切分为 child chunks（200-350 tokens）
    """

    def __init__(
        self,
        parent_min_tokens: int = 600,
        parent_max_tokens: int = 1200,
        child_min_tokens: int = 200,
        child_max_tokens: int = 350,
    ):
        self.parent_min = parent_min_tokens
        self.parent_max = parent_max_tokens
        self.child_min = child_min_tokens
        self.child_max = child_max_tokens
        self._tokenizer = RagTokenizer()

    # ------------------------------------------------------------------
    # 公开入口
    # ------------------------------------------------------------------

    def chunk(
        self,
        text: str,
        doc_id: str = "",
        kb_id: str = "",
        title: str = "",
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        对文本执行父子分块。

        Args:
            text: 原始文本（Markdown 或纯文本）
            doc_id: 文档ID
            kb_id: 知识库ID
            title: 文档标题

        Returns:
            (parent_chunks, child_chunks): 每个 chunk 为 dict，
            含 chunk_id / content / type / chunk_index / char_count 等字段。
            child 额外包含 parent_chunk_id 引用父块。
        """
        if not text or not text.strip():
            return [], []

        sections = self._split_sections(text)
        parents = self._build_parents(sections, doc_id, kb_id, title)
        children = self._split_children(parents, doc_id, kb_id)

        logger.info(
            f"[Chunker] doc={doc_id} 分块完成: "
            f"sections={len(sections)} parents={len(parents)} children={len(children)}"
        )
        return parents, children

    # ------------------------------------------------------------------
    # Section 切分
    # ------------------------------------------------------------------

    def _split_sections(self, text: str) -> List[str]:
        """按 Markdown 标题 / 双换行 / 句子边界逐级切分"""
        # 1. 按 MD 标题分割（保留标题行）
        md_split = re.split(r"(\n#{1,6}\s[^\n]+\n)", text)
        raw_sections = []
        buf = ""
        for part in md_split:
            if re.match(r"\n#{1,6}\s[^\n]+\n", part):
                if buf.strip():
                    raw_sections.append(buf)
                buf = part
            else:
                buf += part
        if buf.strip():
            raw_sections.append(buf)

        # 2. 按双换行进一步拆分
        sections = []
        for sec in raw_sections:
            if self._count_tokens(sec) <= self.parent_max:
                sections.append(sec.strip())
            else:
                for p in re.split(r"\n\s*\n", sec):
                    p = p.strip()
                    if not p:
                        continue
                    if self._count_tokens(p) > self.parent_max:
                        sections.extend(self._split_long_section(p))
                    else:
                        sections.append(p)

        return [s for s in sections if s]

    # ------------------------------------------------------------------
    # 父块构建
    # ------------------------------------------------------------------

    def _build_parents(
        self,
        sections: List[str],
        doc_id: str,
        kb_id: str,
        title: str,
    ) -> List[Dict[str, Any]]:
        """贪心合并 sections，使每个父块在 600-1200 tokens 范围内"""
        parents = []
        buf = []
        buf_tokens = 0

        def flush() -> dict:
            nonlocal buf, buf_tokens
            content = "\n\n".join(buf).strip()
            chunk_id = self._make_chunk_id(doc_id, kb_id, len(parents), "p")
            token_count = self._count_tokens(content)
            buf, buf_tokens = [], 0
            return {
                "chunk_id": chunk_id,
                "content": content,
                "type": "parent",
                "chunk_index": len(parents),
                "page_idx": 0,
                "char_count": len(content),
                "token_count": token_count,
            }

        for sec in sections:
            sec_tokens = self._count_tokens(sec)

            if sec_tokens > self.parent_max:
                if buf:
                    parents.append(flush())
                for sub in self._split_long_section(sec):
                    st = self._count_tokens(sub)
                    if buf_tokens + st > self.parent_max and buf_tokens >= self.parent_min:
                        parents.append(flush())
                    buf.append(sub)
                    buf_tokens += st
                continue

            if buf_tokens + sec_tokens > self.parent_max and buf_tokens >= self.parent_min:
                parents.append(flush())

            buf.append(sec)
            buf_tokens += sec_tokens

        if buf:
            parents.append(flush())

        return parents

    # ------------------------------------------------------------------
    # 子块切分
    # ------------------------------------------------------------------

    def _split_children(
        self,
        parents: List[Dict[str, Any]],
        doc_id: str,
        kb_id: str,
    ) -> List[Dict[str, Any]]:
        """在每个父块内部按句子边界切分子块，不跨父块"""
        children = []
        child_idx = 0

        for parent in parents:
            parent_id = parent["chunk_id"]
            parent_text = parent["content"]
            p_tokens = self._count_tokens(parent_text)

            if p_tokens <= self.child_max:
                children.append(self._make_child(
                    [parent_text], doc_id, kb_id, child_idx, parent_id
                ))
                child_idx += 1
                continue

            sentences = self._split_sentences(parent_text)
            buf, buf_tokens = [], 0

            for sent in sentences:
                st = self._count_tokens(sent)
                if st > self.child_max:
                    if buf:
                        children.append(self._make_child(buf, doc_id, kb_id, child_idx, parent_id))
                        child_idx += 1
                        buf, buf_tokens = [], 0
                    children.append(self._make_child([sent], doc_id, kb_id, child_idx, parent_id))
                    child_idx += 1
                    continue

                if buf_tokens + st > self.child_max and buf_tokens >= self.child_min:
                    children.append(self._make_child(buf, doc_id, kb_id, child_idx, parent_id))
                    child_idx += 1
                    buf, buf_tokens = [], 0

                buf.append(sent)
                buf_tokens += st

            if buf:
                children.append(self._make_child(buf, doc_id, kb_id, child_idx, parent_id))
                child_idx += 1

        return children

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    def _count_tokens(self, text: str) -> int:
        """使用 RagTokenizer 计算 token 数，失败时回退到字符估算"""
        try:
            tokenized = self._tokenizer.tokenize(text)
            return len(tokenized.split()) if tokenized.strip() else 0
        except Exception:
            return max(1, len(text) // 2)

    def _split_long_section(self, text: str) -> List[str]:
        """将超长 section 按句子边界拆分为多个 sub-section"""
        sentences = self._split_sentences(text)
        result = []
        buf, buf_tokens = [], 0
        for sent in sentences:
            st = self._count_tokens(sent)
            if buf_tokens + st > self.parent_max and buf:
                result.append(" ".join(buf))
                buf, buf_tokens = [], 0
            buf.append(sent)
            buf_tokens += st
        if buf:
            result.append(" ".join(buf))
        return result or [text]

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """按中英文句子分隔符切分"""
        parts = re.split(r"(?<=[。！？.!?\n])(?=\s*)", text)
        return [p.strip() for p in parts if p.strip()]

    @staticmethod
    def _make_chunk_id(doc_id: str, kb_id: str, idx: int, prefix: str) -> str:
        uid = str(uuid.uuid4())[:8]
        return f"{kb_id}_{doc_id}_{prefix}{idx}_{uid}"

    def _make_child(
        self,
        sentences: List[str],
        doc_id: str,
        kb_id: str,
        idx: int,
        parent_id: str,
    ) -> Dict[str, Any]:
        content = " ".join(sentences).strip()
        return {
            "chunk_id": self._make_chunk_id(doc_id, kb_id, idx, "c"),
            "content": content,
            "type": "child",
            "parent_chunk_id": parent_id,
            "chunk_index": idx,
            "page_idx": 0,
            "char_count": len(content),
            "token_count": self._count_tokens(content),
        }
