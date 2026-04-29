"""
向后兼容 shim — 从 models 子包重新导出
"""

from models.schemas import (
    SearchRequest,
    ChatRequest,
    AskResponse,
    WriteChatRequest,
)

__all__ = ["SearchRequest", "ChatRequest", "AskResponse", "WriteChatRequest"]
