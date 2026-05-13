
from fastapi import APIRouter
from .search_routes import router as search_router
from .qa_routes import router as qa_router
from .kg_routes import router as kg_router

router = APIRouter()

router.include_router(search_router)
router.include_router(qa_router)
router.include_router(kg_router)

__all__ = ["router"]
