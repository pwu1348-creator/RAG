
from fastapi import APIRouter

from models.schemas import SearchRequest
from core.retriever import SearchService
from utils.logger import logger

router = APIRouter(tags=["检索"])
search_service = SearchService()


@router.post("/search")
async def search_endpoint(request: SearchRequest):
    try:
        results = search_service.search(
            query=request.query,
            knowledge_base_id=request.knowledge_base_id,
            top_k=request.top_k or 10,
            min_score=request.min_score or 0.3,
            use_hybrid=request.use_hybrid if request.use_hybrid is not None else True,
            use_rerank=request.use_rerank if request.use_rerank is not None else True,
        )
        return {"success": True, "results": results, "total": len(results)}
    except Exception as e:
        logger.error(f"[Search API] 检索失败: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
