from typing import Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel

from services.admin_service import admin_service
from utils.response import success_response, error_response

router = APIRouter(tags=["管理员管理"])


class CreateUserRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    phone: Optional[str] = None
    real_name: Optional[str] = None
    department: Optional[str] = None


class UpdateUserRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    real_name: Optional[str] = None
    department: Optional[str] = None
    status: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    new_password: str


class CreateAdminRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    phone: Optional[str] = None
    real_name: Optional[str] = None
    role: str = "admin"


class UpdateAdminRequest(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    real_name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None


@router.get("/dashboard")
async def dashboard():
    stats = admin_service.get_statistics()
    if stats["success"]:
        return success_response(data=stats["data"])
    else:
        return error_response(stats["message"], 500)


@router.get("/statistics")
async def get_statistics():
    stats = admin_service.get_stored_statistics()
    return success_response(data=stats)


@router.post("/statistics/sync")
async def sync_statistics():
    result = admin_service.sync_statistics()
    if result["success"]:
        return success_response(data=result["data"], message="Statistics synced")
    else:
        return error_response(result["message"], 500)


@router.get("/users")
async def list_users(
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1),
    size: int = Query(10)
):
    result = admin_service.list_users(status, keyword, page, size)
    return success_response(data=result)


@router.post("/users")
async def create_user(request: CreateUserRequest):
    result = admin_service.create_user(
        username=request.username,
        password=request.password,
        email=request.email,
        phone=request.phone,
        real_name=request.real_name,
        department=request.department
    )
    if result["success"]:
        return success_response(data=result, message="User created")
    else:
        return error_response(result["message"], 400)


@router.get("/users/{user_id}")
async def get_user(user_id: str):
    user = admin_service.get_user_detail(user_id)
    if user:
        user.pop("password_hash", None)
        return success_response(data=user)
    else:
        return error_response("User not found", 404)


@router.put("/users/{user_id}")
async def update_user(user_id: str, request: UpdateUserRequest):
    update_data = {k: v for k, v in request.dict().items() if v is not None}
    if not update_data:
        return error_response("No valid fields to update", 400)
    result = admin_service.update_user(user_id, **update_data)
    if result["success"]:
        return success_response(message="User updated")
    else:
        return error_response(result["message"], 400)


@router.post("/users/{user_id}/password")
async def reset_user_password(user_id: str, request: ResetPasswordRequest):
    result = admin_service.reset_user_password(user_id, request.new_password)
    if result["success"]:
        return success_response(message="Password reset")
    else:
        return error_response(result["message"], 400)


@router.post("/users/{user_id}/lock")
async def lock_user(user_id: str):
    result = admin_service.lock_user(user_id)
    if result["success"]:
        return success_response(message="User locked")
    else:
        return error_response(result["message"], 400)


@router.post("/users/{user_id}/unlock")
async def unlock_user(user_id: str):
    result = admin_service.unlock_user(user_id)
    if result["success"]:
        return success_response(message="User unlocked")
    else:
        return error_response(result["message"], 400)


@router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    result = admin_service.delete_user(user_id)
    if result["success"]:
        return success_response(message="User deleted")
    else:
        return error_response(result["message"], 400)


@router.get("/admins")
async def list_admins(
    status: Optional[str] = Query(None),
    page: int = Query(1),
    size: int = Query(10)
):
    result = admin_service.list_admins(status, page, size)
    return success_response(data=result)


@router.post("/admins")
async def create_admin(request: CreateAdminRequest):
    result = admin_service.create_admin(
        username=request.username,
        password=request.password,
        email=request.email,
        phone=request.phone,
        real_name=request.real_name,
        role=request.role
    )
    if result["success"]:
        return success_response(data=result, message="Admin created")
    else:
        return error_response(result["message"], 400)


@router.get("/admins/{admin_id}")
async def get_admin(admin_id: str):
    admin = admin_service.get_admin_detail(admin_id)
    if admin:
        admin.pop("password_hash", None)
        return success_response(data=admin)
    else:
        return error_response("Admin not found", 404)


@router.put("/admins/{admin_id}")
async def update_admin(admin_id: str, request: UpdateAdminRequest):
    update_data = {k: v for k, v in request.dict().items() if v is not None}
    if not update_data:
        return error_response("No valid fields to update", 400)
    result = admin_service.update_admin(admin_id, **update_data)
    if result["success"]:
        return success_response(message="Admin updated")
    else:
        return error_response(result["message"], 400)


@router.delete("/admins/{admin_id}")
async def delete_admin(admin_id: str):
    result = admin_service.delete_admin(admin_id)
    if result["success"]:
        return success_response(message="Admin deleted")
    else:
        return error_response(result["message"], 400)
