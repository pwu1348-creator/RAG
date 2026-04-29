"""
路由聚合模块

将 search / qa / index 三个子路由合并为一个 router，
供 main.py 直接挂载。
"""

from fastapi import APIRouter
from .search_routes import router as search_router
from .qa_routes import router as qa_router
from .index_routes import router as index_router
from .auth_routes import router as auth_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(search_router)
router.include_router(qa_router)
router.include_router(index_router)

__all__ = ["router"]
