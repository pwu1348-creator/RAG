
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from config import config
from services.knowledge_graph_service import KnowledgeGraphService
from services.entity_relation_extractor import EntityRelationExtractor
from utils.logger import logger

router = APIRouter(tags=["知识图谱"])
kg_service = KnowledgeGraphService()
extractor = EntityRelationExtractor()


class ExtractRequest(BaseModel):
    doc_id: str
    kb_id: str
    content: str
    chunk_size: int = 2000


class EntitySearchRequest(BaseModel):
    name: str
    limit: int = 10


class MultiHopSearchRequest(BaseModel):
    entity_name: str
    hops: int = 2
    limit: int = 50


class DeleteKBRequest(BaseModel):
    kb_id: str


@router.post("/kg/extract")
async def extract_entities_and_relations(request: ExtractRequest, background_tasks: BackgroundTasks):
    if not kg_service.is_enabled():
        raise HTTPException(status_code=503, detail="知识图谱服务未启用")
    
    try:
        background_tasks.add_task(
            extractor.extract_from_document,
            request.doc_id,
            request.kb_id,
            request.content,
            request.chunk_size
        )
        
        return {
            "status": "success",
            "message": "已提交提取任务，在后台执行",
            "doc_id": request.doc_id,
        }
    
    except Exception as e:
        logger.error(f"[/kg/extract] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kg/extract/sync")
async def extract_entities_and_relations_sync(request: ExtractRequest):
    if not kg_service.is_enabled():
        raise HTTPException(status_code=503, detail="知识图谱服务未启用")
    
    try:
        entities, relations = await extractor.extract_from_document(
            request.doc_id,
            request.kb_id,
            request.content,
            request.chunk_size
        )
        
        return {
            "status": "success",
            "entities": [
                {
                    "id": e.id,
                    "name": e.name,
                    "type": e.entity_type,
                    "doc_ids": e.doc_ids,
                }
                for e in entities
            ],
            "relations": [
                {
                    "id": r.id,
                    "source_id": r.source_id,
                    "target_id": r.target_id,
                    "relation_type": r.relation_type,
                    "confidence": r.confidence,
                    "doc_ids": r.doc_ids,
                }
                for r in relations
            ],
            "entity_count": len(entities),
            "relation_count": len(relations),
        }
    
    except Exception as e:
        logger.error(f"[/kg/extract/sync] 错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kg/search/entity")
async def search_entity(request: EntitySearchRequest):
    if not kg_service.is_enabled():
        raise HTTPException(status_code=503, detail="知识图谱服务未启用")
    
    try:
        entities = kg_service.search_entity(request.name, request.limit)
        
        return {
            "status": "success",
            "entities": [
                {
                    "id": e.id,
                    "name": e.name,
                    "type": e.entity_type,
                    "doc_ids": e.doc_ids,
                    "properties": e.properties,
                }
                for e in entities
            ],
            "total": len(entities),
        }
    
    except Exception as e:
        logger.error(f"[/kg/search/entity] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kg/search/multihop")
async def search_multihop(request: MultiHopSearchRequest):
    if not kg_service.is_enabled():
        raise HTTPException(status_code=503, detail="知识图谱服务未启用")
    
    try:
        result = kg_service.multi_hop_search(
            request.entity_name,
            request.hops,
            request.limit
        )
        
        return {
            "status": "success",
            "query_entity": request.entity_name,
            "hops": request.hops,
            "entities": result.get("entities", []),
            "relations": result.get("relations", []),
            "entity_count": len(result.get("entities", [])),
            "relation_count": len(result.get("relations", [])),
        }
    
    except Exception as e:
        logger.error(f"[/kg/search/multihop] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kg/delete/kb")
async def delete_kb_graph(request: DeleteKBRequest):
    if not kg_service.is_enabled():
        raise HTTPException(status_code=503, detail="知识图谱服务未启用")
    
    try:
        success = kg_service.delete_kb_data(request.kb_id)
        
        if success:
            return {
                "status": "success",
                "message": f"已删除知识库 {request.kb_id} 的所有图数据",
                "kb_id": request.kb_id,
            }
        else:
            raise HTTPException(status_code=500, detail="删除失败")
    
    except Exception as e:
        logger.error(f"[/kg/delete/kb] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kg/status")
async def get_kg_status():
    try:
        return {
            "status": "success",
            "kg_enabled": kg_service.is_enabled(),
            "kg_backend": config.kg.BACKEND if kg_service.is_enabled() else "disabled",
            "min_confidence": config.kg.MIN_CONFIDENCE,
            "hop_limit": config.kg.HOP_LIMIT,
            "max_entities_per_doc": config.kg.MAX_ENTITIES_PER_DOC,
            "max_relations_per_doc": config.kg.MAX_RELATIONS_PER_DOC,
        }
    
    except Exception as e:
        logger.error(f"[/kg/status] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))
