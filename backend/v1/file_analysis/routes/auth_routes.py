import os
import uuid
from typing import Optional

from fastapi import APIRouter, File, Request, UploadFile
from pydantic import BaseModel

from services.auth_service import auth_service
from services.admin_service import admin_service
from utils.response import success_response, error_response
from utils.logger import logger

router = APIRouter(tags=["认证"])


class LoginRequest(BaseModel):
    username: str
    password: str


class AdminRegisterRequest(BaseModel):
    username: str
    password: str
    email: str = None
    phone: str = None
    real_name: str = None
    role: str = "admin"


class UpdateProfileRequest(BaseModel):
    username: Optional[str] = None
    old_password: Optional[str] = None
    password: Optional[str] = None


@router.post("/admin/login")
async def admin_login(request: Request, login_data: LoginRequest):
    logger.info(f"admin_login called: {login_data.username}")
    result = auth_service.admin_login(
        username=login_data.username,
        password=login_data.password,
        login_ip=request.client.host,
        user_agent=request.headers.get("User-Agent")
    )

    if result["success"]:
        return success_response(data=result, message="Login successful")
    else:
        return error_response(result["message"], 401)


@router.post("/user/login")
async def user_login(request: Request, login_data: LoginRequest):
    result = auth_service.user_login(
        username=login_data.username,
        password=login_data.password,
        login_ip=request.client.host,
        user_agent=request.headers.get("User-Agent")
    )

    if result["success"]:
        return success_response(data=result, message="Login successful")
    else:
        return error_response(result["message"], 401)


@router.post("/logout")
async def logout(request: Request):
    token = request.headers.get("Authorization")
    if token and token.startswith("Bearer "):
        token = token[7:]

    if token:
        auth_service.logout(token)

    return success_response(message="Logout successful")


@router.post("/admin/register")
async def admin_register(request: Request, register_data: AdminRegisterRequest):
    result = admin_service.create_admin(
        username=register_data.username,
        password=register_data.password,
        email=register_data.email,
        phone=register_data.phone,
        real_name=register_data.real_name,
        role=register_data.role
    )

    if result["success"]:
        return success_response(data=result, message="Admin created")
    else:
        return error_response(result["message"], 400)


def _get_user_from_token(request: Request):
    token = request.headers.get("Authorization", "")
    if token.startswith("Bearer "):
        token = token[7:]
    if not token:
        return None
    payload = auth_service.verify_token(token)
    if not payload:
        return None
    return payload


@router.get("/user/info")
async def get_user_info(request: Request):
    payload = _get_user_from_token(request)
    if not payload:
        return error_response("未登录或 token 无效", 401)

    user_id = payload.get("user_id")
    if not user_id:
        return error_response("无效的用户 token", 401)

    from database.db_manager import DatabaseManager
    db = DatabaseManager()
    user = db.get_user_by_id(user_id)
    if not user:
        return error_response("用户不存在", 404)

    user.pop("password_hash", None)
    return success_response(data=user)


@router.put("/user/info")
async def update_user_info(request: Request, body: UpdateProfileRequest):
    payload = _get_user_from_token(request)
    if not payload:
        return error_response("未登录或 token 无效", 401)

    user_id = payload.get("user_id")
    if not user_id:
        return error_response("无效的用户 token", 401)

    from database.db_manager import DatabaseManager
    db = DatabaseManager()

    if body.username:
        existing = db.get_user_by_username(body.username)
        if existing and existing.get("user_id") != user_id:
            return error_response("用户名已被占用", 400)
        db.update_user(user_id, username=body.username)

    if body.password:
        if not body.old_password:
            return error_response("修改密码需要提供原密码", 400)
        user = db.get_user_by_id(user_id)
        if not user:
            return error_response("用户不存在", 404)
        if not db.verify_password(body.old_password, user.get("password_hash", "")):
            return error_response("原密码错误", 400)
        db.update_user_password(user_id, body.password)

    return success_response(message="修改成功")


@router.post("/user/avatar")
async def upload_user_avatar(request: Request, file: UploadFile = File(...)):
    payload = _get_user_from_token(request)
    if not payload:
        return error_response("未登录或 token 无效", 401)

    user_id = payload.get("user_id")
    if not user_id:
        return error_response("无效的用户 token", 401)

    if not file.filename:
        return error_response("文件为空", 400)

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ('.png', '.jpg', '.jpeg', '.gif', '.webp'):
        return error_response("仅支持 png/jpg/jpeg/gif/webp 格式", 400)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    avatar_dir = os.path.join(base_dir, "uploads", "avatars")
    os.makedirs(avatar_dir, exist_ok=True)

    avatar_filename = f"user_{user_id}_{uuid.uuid4().hex[:8]}{ext}"
    avatar_path = os.path.join(avatar_dir, avatar_filename)

    content = await file.read()
    with open(avatar_path, "wb") as f:
        f.write(content)

    avatar_url = f"/uploads/avatars/{avatar_filename}"

    from database.db_manager import DatabaseManager
    db = DatabaseManager()
    db.update_user(user_id, avatar_url=avatar_url)

    return success_response(data={"avatar_url": avatar_url}, message="头像上传成功")
