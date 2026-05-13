from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel

from services.settings_service import settings_service
from services.auth_service import auth_service
from utils.response import success_response, error_response

router = APIRouter(tags=["系统设置"])


async def get_current_admin(request: Request):
    token = request.headers.get("Authorization")
    if token and token.startswith("Bearer "):
        token = token[7:]
    token_data = auth_service.verify_token(token)
    if not token_data or token_data.get("type") != "admin":
        return None
    return token_data


class UpdateSettingRequest(BaseModel):
    value: str
    type: Optional[str] = None


class BatchUpdateSettingsRequest(BaseModel):
    settings: List[dict]


class CreateApiConfigRequest(BaseModel):
    name: str
    api_type: str
    provider: str
    base_url: str
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    max_tokens: int = 2048
    timeout: int = 30
    is_default: bool = False
    config: Optional[dict] = None


class UpdateRetrievalSettingsRequest(BaseModel):
    kb_id: Optional[str] = None
    search_type: Optional[str] = None
    top_k: Optional[int] = None
    similarity_threshold: Optional[float] = None
    rerank_enabled: Optional[bool] = None
    rerank_model: Optional[str] = None
    keyword_weight: Optional[float] = None
    semantic_weight: Optional[float] = None


@router.get("")
async def get_all_settings(current_admin: dict = Depends(get_current_admin)):
    if not current_admin:
        return error_response("Admin access required", 403)
    settings = settings_service.get_all_settings()
    return success_response(data=settings)


@router.get("/system-info")
async def get_system_info():
    info = settings_service.get_system_info()
    return success_response(data=info)


@router.get("/{category}")
async def get_settings_by_category(category: str, current_admin: dict = Depends(get_current_admin)):
    if not current_admin:
        return error_response("Admin access required", 403)
    settings = settings_service.get_settings_by_category(category)
    return success_response(data=settings)


@router.get("/{category}/{key}")
async def get_setting(category: str, key: str, current_admin: dict = Depends(get_current_admin)):
    if not current_admin:
        return error_response("Admin access required", 403)
    setting = settings_service.get_setting_detail(category, key)
    if setting:
        return success_response(data=setting)
    return error_response("Setting not found", 404)


@router.put("/{category}/{key}")
async def update_setting(
    category: str,
    key: str,
    request: UpdateSettingRequest,
    current_admin: dict = Depends(get_current_admin)
):
    if not current_admin:
        return error_response("Admin access required", 403)
    result = settings_service.set_setting(category, key, request.value, request.type)
    if result["success"]:
        return success_response(message="Setting updated")
    else:
        return error_response(result["message"], 400)


@router.put("/batch")
async def update_settings_batch(
    request: BatchUpdateSettingsRequest,
    current_admin: dict = Depends(get_current_admin)
):
    if not current_admin:
        return error_response("Admin access required", 403)
    result = settings_service.update_settings_batch(request.settings)
    if result["success"]:
        return success_response(data=result, message="Settings updated")
    else:
        return success_response(data=result, message="Some settings failed to update")


@router.get("/api-configs")
async def list_api_configs(
    api_type: Optional[str] = Query(None),
    active: Optional[bool] = Query(None),
    current_admin: dict = Depends(get_current_admin)
):
    if not current_admin:
        return error_response("Admin access required", 403)
    configs = settings_service.list_api_configs(api_type, active)
    return success_response(data=configs)


@router.post("/api-configs")
async def create_api_config(
    request: CreateApiConfigRequest,
    current_admin: dict = Depends(get_current_admin)
):
    if not current_admin:
        return error_response("Admin access required", 403)
    result = settings_service.create_api_config(
        admin_id=current_admin["id"],
        name=request.name,
        api_type=request.api_type,
        provider=request.provider,
        base_url=request.base_url,
        api_key=request.api_key,
        model_name=request.model_name,
        max_tokens=request.max_tokens,
        timeout=request.timeout,
        is_default=request.is_default,
        config=request.config
    )
    if result["success"]:
        return success_response(data=result, message="API config created")
    else:
        return error_response(result["message"], 400)


@router.get("/api-configs/{api_id}")
async def get_api_config(
    api_id: str,
    include_key: bool = Query(False),
    current_admin: dict = Depends(get_current_admin)
):
    if not current_admin:
        return error_response("Admin access required", 403)
    config = settings_service.get_api_config(api_id, include_key)
    if config:
        return success_response(data=config)
    return error_response("API config not found", 404)


@router.put("/api-configs/{api_id}")
async def update_api_config(
    api_id: str,
    request: dict,
    current_admin: dict = Depends(get_current_admin)
):
    if not current_admin:
        return error_response("Admin access required", 403)
    result = settings_service.update_api_config(current_admin["id"], api_id, **request)
    if result["success"]:
        return success_response(message="API config updated")
    else:
        return error_response(result["message"], 400)


@router.delete("/api-configs/{api_id}")
async def delete_api_config(api_id: str, current_admin: dict = Depends(get_current_admin)):
    if not current_admin:
        return error_response("Admin access required", 403)
    result = settings_service.delete_api_config(current_admin["id"], api_id)
    if result["success"]:
        return success_response(message="API config deleted")
    else:
        return error_response(result["message"], 400)


@router.post("/api-configs/{api_id}/default")
async def set_default_api_config(api_id: str, current_admin: dict = Depends(get_current_admin)):
    if not current_admin:
        return error_response("Admin access required", 403)
    result = settings_service.set_default_api_config(current_admin["id"], api_id)
    if result["success"]:
        return success_response(message="Default API config set")
    else:
        return error_response(result["message"], 400)


@router.get("/retrieval")
async def get_retrieval_settings(
    kb_id: Optional[str] = Query(None),
    current_admin: dict = Depends(get_current_admin)
):
    if not current_admin:
        return error_response("Admin access required", 403)
    settings = settings_service.get_retrieval_settings(kb_id)
    if settings:
        return success_response(data=settings)
    return success_response(data={
        "search_type": "semantic",
        "top_k": 5,
        "similarity_threshold": 0.7,
        "rerank_enabled": False,
        "rerank_model": None,
        "keyword_weight": 0.3,
        "semantic_weight": 0.7
    })


@router.put("/retrieval")
async def update_retrieval_settings(
    request: UpdateRetrievalSettingsRequest,
    current_admin: dict = Depends(get_current_admin)
):
    if not current_admin:
        return error_response("Admin access required", 403)
    update_data = {k: v for k, v in request.dict().items() if v is not None and k != "kb_id"}
    result = settings_service.set_retrieval_settings(current_admin["id"], request.kb_id, **update_data)
    if result["success"]:
        return success_response(message="Retrieval settings updated")
    else:
        return error_response(result["message"], 400)
