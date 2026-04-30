"""
路由聚合模块

将 search / qa / index / kg 子路由合并为一个 router，
供 main.py 以 /api/v1/search 前缀挂载。
auth_router 由 main.py 单独以 /api/v1 前缀挂载，不在此聚合。
"""

from fastapi import APIRouter
from .search_routes import router as search_router
from .qa_routes import router as qa_router
from .index_routes import router as index_router
from .kg_routes import router as kg_router

router = APIRouter()

router.include_router(search_router)
router.include_router(qa_router)
router.include_router(index_router)
router.include_router(kg_router)

__all__ = ["router"]
