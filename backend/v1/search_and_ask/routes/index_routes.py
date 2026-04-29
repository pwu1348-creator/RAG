"""
索引管理路由 — 触发文档父子重索引
"""

from fastapi import APIRouter, HTTPException

from services.indexing import IndexService
from core.retriever import SearchService
from utils.logger import logger

router = APIRouter(tags=["索引管理"])
index_service = IndexService()
search_service = SearchService()


@router.post("/index/kb/{kb_id}")
async def reindex_knowledge_base(kb_id: str):
    """
    重索整个知识库

    将知识库中所有文档按父子分块策略重新索引：
    - 父块 (600-1200 tokens) → MySQL
    - 子块 (200-350 tokens) → MySQL + ChromaDB
    - 子块携带 parent_chunk_id，检索后可回退父块完整上下文
    """
    try:
        result = index_service.reindex_knowledge_base(kb_id)
        search_service.reset()
        return result
    except Exception as e:
        logger.error(f"[Index API] 知识库重索引失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index/doc/{kb_id}/{doc_id}")
async def reindex_document(kb_id: str, doc_id: str):
    """
    重索单个文档

    将该文档的旧 chunks 替换为父子分块结构。
    """
    try:
        p, c = index_service.reindex_document(doc_id, kb_id)
        search_service.reset()
        return {
            "success": True,
            "doc_id": doc_id,
            "kb_id": kb_id,
            "parents": p,
            "children": c,
        }
    except Exception as e:
        logger.error(f"[Index API] 文档重索引失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
