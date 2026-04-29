"""
Search & Ask Service v2.0

目录结构：
  core/       — 核心业务逻辑（检索、问答、分块）
  routes/     — API 路由（search / qa / index）
  services/   — 服务层（文档重索引）
  models/     — Pydantic 数据模型
  main.py     — FastAPI 入口
"""

from .core import (
    SearchService,
    HybridRetriever,
    BM25Retriever,
    Reranker,
    ParentChildRetriever,
    ParentChildChunker,
    QuestionAnswering,
)
from .services import IndexService
from .routes import router

__all__ = [
    # 核心
    "SearchService",
    "HybridRetriever",
    "BM25Retriever",
    "Reranker",
    "ParentChildRetriever",
    "ParentChildChunker",
    "QuestionAnswering",
    # 服务
    "IndexService",
    # 路由
    "router",
]
