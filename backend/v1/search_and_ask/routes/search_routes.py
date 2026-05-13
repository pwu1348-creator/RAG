"""
检索路由 — 纯搜索，不调用 LLM
"""

from fastapi import APIRouter

from models.schemas import SearchRequest
from core.retriever import SearchService
from utils.logger import logger

router = APIRouter(tags=["检索"])
search_service = SearchService()


@router.post("/search")
async def search_endpoint(request: SearchRequest):
    """
    检索接口

    流程: query → 混合检索(BM25+向量+RRF) → BGE重排 → 返回结果
    不调用 LLM，仅返回相关段落。
    """
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
