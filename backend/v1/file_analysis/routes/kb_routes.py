from typing import Optional
import os
import uuid
from fastapi import APIRouter, Query
from pydantic import BaseModel

from services.admin_service import admin_service
from services.parser_service import ParserService
from services.mysql_service import MySQLService
from services.chromadb_service import chromadb_service
from utils.response import success_response, error_response
from utils.logger import logger

router = APIRouter(tags=["知识库管理"])
parser_service = ParserService()
mysql_service = MySQLService()


class CreateKBRequest(BaseModel):
    name: str
    description: Optional[str] = None
    embedding_model: Optional[str] = None
    vector_dimension: int = 1024
    owner_id: Optional[str] = None
    owner_type: Optional[str] = None


class BatchParseRequest(BaseModel):
    doc_ids: list[str]


class UpdateKBRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    owner_type: Optional[str] = None
    owner_id: Optional[str] = None


class AddUserToKBRequest(BaseModel):
    user_id: str
    role: str = "viewer"


class UpdateUserRoleRequest(BaseModel):
    role: str


@router.get("")
async def list_knowledge_bases(
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1),
    size: int = Query(10)
):
    result = admin_service.list_knowledge_bases(status, keyword, page, size)
    return success_response(data=result)


@router.post("")
async def create_knowledge_base(request: CreateKBRequest):
    result = admin_service.create_knowledge_base(
        admin_id="system",
        name=request.name,
        description=request.description,
        embedding_model=request.embedding_model,
        vector_dimension=request.vector_dimension,
        owner_id=request.owner_id,
        owner_type=request.owner_type
    )
    if result["success"]:
        return success_response(data=result, message="Knowledge base created")
    else:
        return error_response(result["message"], 400)


@router.get("/{kb_id}")
async def get_knowledge_base(kb_id: str):
    kb = admin_service.get_knowledge_base_detail(kb_id)
    if kb:
        return success_response(data=kb)
    else:
        return error_response("Knowledge base not found", 404)


@router.put("/{kb_id}")
async def update_knowledge_base(kb_id: str, request: UpdateKBRequest):
    nullable_fields = {'owner_type', 'owner_id'}
    raw = request.dict()
    update_data = {}
    for k, v in raw.items():
        if v is not None:
            update_data[k] = v
        elif k in nullable_fields:
            update_data[k] = None
    if not update_data:
        return error_response("No valid fields to update", 400)
    result = admin_service.update_knowledge_base("system", kb_id, **update_data)
    if result["success"]:
        return success_response(message="Knowledge base updated")
    else:
        return error_response(result["message"], 400)


@router.delete("/{kb_id}")
async def delete_knowledge_base(kb_id: str):
    kb = admin_service.get_knowledge_base_detail(kb_id)
    tenant_id = kb.get("owner_id", "") if kb else ""
    
    try:
        if tenant_id:
            chromadb_service.delete_collection(tenant_id)
    except Exception as e:
        logger.warning(f"Failed to delete collection: {e}")
    
    mysql_service.delete_kb_all_relations(kb_id)
    
    result = admin_service.delete_knowledge_base("system", kb_id)
    if result["success"]:
        return success_response(message="Knowledge base deleted")
    else:
        return error_response(result["message"], 400)


@router.get("/{kb_id}/users")
async def list_kb_users(
    kb_id: str,
    page: int = Query(1),
    size: int = Query(10)
):
    result = admin_service.list_kb_users(kb_id, page, size)
    return success_response(data=result)


@router.post("/{kb_id}/users")
async def add_user_to_kb(kb_id: str, request: AddUserToKBRequest):
    result = admin_service.add_user_to_kb("system", request.user_id, kb_id, request.role)
    if result["success"]:
        return success_response(message="User added to knowledge base")
    else:
        return error_response(result["message"], 400)


@router.put("/{kb_id}/users/{user_id}")
async def update_user_role(kb_id: str, user_id: str, request: UpdateUserRoleRequest):
    result = admin_service.update_user_kb_role("system", user_id, kb_id, request.role)
    if result["success"]:
        return success_response(message="User role updated")
    else:
        return error_response(result["message"], 400)


@router.delete("/{kb_id}/users/{user_id}")
async def remove_user_from_kb(kb_id: str, user_id: str):
    result = admin_service.remove_user_from_kb("system", user_id, kb_id)
    if result["success"]:
        return success_response(message="User removed from knowledge base")
    else:
        return error_response(result["message"], 400)


@router.get("/users/{user_id}/kbs")
async def list_user_knowledge_bases(
    user_id: str,
    page: int = Query(1),
    size: int = Query(10)
):
    result = admin_service.list_user_kbs(user_id, page, size)
    return success_response(data=result)


@router.get("/{kb_id}/documents")
async def list_kb_documents(
    kb_id: str,
    page: int = Query(1),
    size: int = Query(10),
    status: Optional[str] = Query(None)
):
    result = mysql_service.list_kb_documents(kb_id, status=status, page=page, size=size)
    return success_response(data=result)


@router.get("/{kb_id}/documents/{doc_id}")
async def get_kb_document(kb_id: str, doc_id: str):
    doc = admin_service.get_kb_document(kb_id, doc_id)
    if doc:
        return success_response(data=doc)
    else:
        return error_response("Document not found", 404)


@router.delete("/{kb_id}/collection")
async def delete_kb_collection(kb_id: str):
    try:
        kb = admin_service.get_knowledge_base_detail(kb_id)
        tenant_id = kb.get("owner_id", "") if kb else ""
        if tenant_id:
            chromadb_service.delete_collection(tenant_id)
        return success_response(message="Collection deleted")
    except Exception as e:
        return error_response(str(e), 400)


@router.get("/files/unlinked")
async def list_unlinked_files(
    page: int = Query(1),
    size: int = Query(10)
):
    files = mysql_service.list_unlinked_documents(page=page, size=size)
    return success_response(data=files)


@router.post("/{kb_id}/files/{doc_id}")
async def associate_file_to_kb(kb_id: str, doc_id: str):
    doc = parser_service.get_document(doc_id)
    if not doc:
        return error_response("Document not found", 404)
    
    success = mysql_service.associate_document_to_kb(kb_id, doc_id)
    if success:
        return success_response(message="File associated to knowledge base")
    else:
        return error_response("Failed to associate file", 500)


@router.delete("/{kb_id}/files/{doc_id}")
async def remove_file_from_kb(kb_id: str, doc_id: str):
    doc = parser_service.get_document(doc_id)
    if not doc:
        return error_response("Document not found", 404)
    
    kb = admin_service.get_knowledge_base_detail(kb_id)
    tenant_id = kb.get("owner_id", "") if kb else ""
    
    try:
        if tenant_id:
            chromadb_service.delete_document_chunks(tenant_id, kb_id, doc_id)
    except Exception as e:
        logger.warning(f"Failed to delete vectors: {e}")
    
    success = mysql_service.remove_document_from_kb(kb_id, doc_id)
    if success:
        mysql_service.refresh_kb_statistics(kb_id)
        return success_response(message="File removed from knowledge base")
    else:
        return error_response("Failed to remove file", 500)


@router.post("/{kb_id}/documents/{doc_id}/parse")
async def parse_kb_document(kb_id: str, doc_id: str):
    doc = parser_service.get_document(doc_id)
    if not doc:
        return error_response("Document not found", 404)
    
    try:
        task_id = str(uuid.uuid4())

        mysql_service.update_kb_document_status(kb_id, doc_id, 'processing')
        
        kb = admin_service.get_knowledge_base_detail(kb_id)
        tenant_id = kb.get("owner_id", "") if kb else ""
        
        minio_object = doc.get('minio_object')
        if not minio_object:
            return error_response("File path not found", 400)
        
        file_path = minio_object
        if not os.path.isabs(file_path) and not file_path.startswith('uploads'):
            file_path = os.path.join('uploads', minio_object)
        
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}, minio_object: {minio_object}, minio_url: {doc.get('minio_url')}")
            return error_response(f"File not found: {file_path}", 404)
        
        parser_service.create_task(
            task_id=task_id,
            filename=doc.get('filename', 'unknown'),
            file_path=file_path,
            kb_id=kb_id,
            doc_id=doc_id,
            tenant_id=tenant_id,
            sequential=True,
        )

        return success_response(message="Document parsing started")
    except Exception as e:
        logger.error(f"Parse document error: {e}")
        return error_response(str(e), 500)


@router.post("/{kb_id}/documents/parse")
async def batch_parse_kb_documents(kb_id: str, req: BatchParseRequest):
    if not req.doc_ids:
        return error_response("doc_ids is required", 400)

    kb = admin_service.get_knowledge_base_detail(kb_id)
    tenant_id = kb.get("owner_id", "") if kb else ""

    success_count = 0
    fail_count = 0
    errors = []

    for doc_id in req.doc_ids:
        doc = parser_service.get_document(doc_id)
        if not doc:
            errors.append({"doc_id": doc_id, "error": "Document not found"})
            fail_count += 1
            continue

        try:
            task_id = str(uuid.uuid4())

            mysql_service.update_kb_document_status(kb_id, doc_id, 'processing')

            minio_object = doc.get('minio_object')
            if not minio_object:
                errors.append({"doc_id": doc_id, "error": "File path not found"})
                fail_count += 1
                continue

            file_path = minio_object
            if not os.path.isabs(file_path) and not file_path.startswith('uploads'):
                file_path = os.path.join('uploads', minio_object)

            if not os.path.exists(file_path):
                errors.append({"doc_id": doc_id, "error": f"File not found: {file_path}"})
                fail_count += 1
                continue

            parser_service.create_task(
                task_id=task_id,
                filename=doc.get('filename', 'unknown'),
                file_path=file_path,
                kb_id=kb_id,
                doc_id=doc_id,
                tenant_id=tenant_id,
                sequential=True,
            )
            success_count += 1
        except Exception as e:
            logger.error(f"Batch parse error for {doc_id}: {e}")
            errors.append({"doc_id": doc_id, "error": str(e)})
            fail_count += 1

    return success_response(
        message=f"Batch parse completed: {success_count} success, {fail_count} failed",
        data={
            "success_count": success_count,
            "fail_count": fail_count,
            "errors": errors
        }
    )
