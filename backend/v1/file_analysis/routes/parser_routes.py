import os
import uuid
import json
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse

from config import config
from services.parser_service import ParserService
from services.mysql_service import MySQLService
from models.document import DocumentMetadata
from core.document_parser import SUPPORTED_ENGINES
from utils.response import success_response, error_response
from utils.validators import validate_file
from utils.logger import logger

router = APIRouter(tags=["文档解析"])
parser_service = ParserService()
mysql_service = MySQLService()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    options: str = Form("{}")
):
    if not file.filename:
        return error_response("Empty filename", 400)

    is_valid, error_msg = await validate_file(file)
    if not is_valid:
        return error_response(error_msg, 400)

    filename = file.filename
    task_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{task_id}_{filename}")

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    file_size = len(content)
    file_type = os.path.splitext(filename)[1].lower()

    metadata = DocumentMetadata(
        doc_id=doc_id,
        filename=filename,
        file_type=file_type,
        file_size=file_size,
        minio_url=file_path,
        minio_bucket='local',
        minio_object=f"{task_id}_{filename}",
        total_pages=0,
        total_chunks=0,
        text_length=0,
        status='completed',
        extra_metadata=json.dumps({})
    )
    mysql_service.create_document(metadata)

    task = parser_service.create_task(
        task_id=task_id,
        filename=filename,
        file_path=file_path,
        options=options
    )

    logger.info(f"Created task: {task_id}, file: {filename}")

    return success_response(
        data=task.to_dict(),
        message="File uploaded, processing started"
    )


@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    task = parser_service.get_task(task_id)
    if not task:
        return error_response("Task not found", 404)
    return success_response(data=task.to_dict())


@router.delete("/task/{task_id}")
async def delete_task(task_id: str):
    success = parser_service.delete_task(task_id)
    if not success:
        return error_response("Task not found", 404)
    logger.info(f"Deleted task: {task_id}")
    return success_response(message="Task deleted")


@router.get("/tasks")
async def list_tasks(
    status: Optional[str] = Query(None),
    page: int = Query(1),
    size: int = Query(10)
):
    tasks = parser_service.list_tasks(status=status, page=page, size=size)
    return success_response(data=tasks)


@router.get("/documents")
async def list_documents(
    user_id: Optional[str] = Query(None),
    knowledge_base_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1),
    size: int = Query(10)
):
    documents = parser_service.list_documents(
        user_id=user_id,
        knowledge_base_id=knowledge_base_id,
        status=status,
        page=page,
        size=size
    )
    return success_response(data=documents)


@router.get("/document/{doc_id}")
async def get_document(doc_id: str):
    document = parser_service.get_document(doc_id)
    if not document:
        return error_response("Document not found", 404)
    return success_response(data=document)


@router.delete("/document/{doc_id}")
async def delete_document(doc_id: str):
    document = parser_service.get_document(doc_id)
    if not document:
        return error_response("Document not found", 404)

    task_id = document.get('task_id')
    if task_id:
        parser_service.delete_task(task_id)
    else:
        parser_service.mysql.delete_document(doc_id)

    logger.info(f"Deleted document: {doc_id}")
    return success_response(message="Document deleted")


@router.get("/supported-formats")
async def get_supported_formats():
    return success_response(data={
        'extensions': config.parser.SUPPORTED_EXTENSIONS,
        'max_size_mb': config.parser.MAX_FILE_SIZE
    })


# ==================== 解析引擎管理 ====================

@router.get("/parse-engine")
async def get_parse_engine():
    """获取当前解析引擎配置"""
    return success_response(data={
        'current_engine': config.mineru.PARSE_ENGINE,
        'supported_engines': list(SUPPORTED_ENGINES),
        'engine_descriptions': {
            'pipeline': '管道普通模式 - 使用传统 OCR + 布局分析管道，适合大多数文档',
            'vlm': 'VLM模式 - 使用视觉语言模型解析，适合复杂版面文档（需要 VLM 模型）',
            'hybrid': '混合模式 - 结合 pipeline 和 VLM 的优势，自动选择最佳策略（需要 VLM 模型）',
        }
    })


@router.put("/parse-engine")
async def set_parse_engine(request: dict):
    """切换解析引擎模式"""
    engine = request.get('engine', '').lower().strip()
    if engine not in SUPPORTED_ENGINES:
        return error_response(
            f"不支持的引擎: {engine}，可选值: {', '.join(SUPPORTED_ENGINES)}", 400
        )
    config.mineru.PARSE_ENGINE = engine
    logger.info(f"[Parser-INFO] 解析引擎已切换为: {engine}")
    return success_response(
        data={'current_engine': engine},
        message=f"解析引擎已切换为: {engine}"
    )
