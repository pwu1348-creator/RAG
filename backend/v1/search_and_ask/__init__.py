"""
Search & Ask Service v2.0

目录结构：
  core/       — 核心业务逻辑（检索、问答）
  routes/     — API 路由（search / qa / kg）
  services/   — 服务层
  models/     — Pydantic 数据模型
  main.py     — FastAPI 入口
"""

from .core import (
    SearchService,
    HybridRetriever,
    BM25Retriever,
    Reranker,
    QuestionAnswering,
)
from .routes import router

__all__ = [
    # 核心
    "SearchService",
    "HybridRetriever",
    "BM25Retriever",
    "Reranker",
    "QuestionAnswering",
    # 路由
    "router",
]
