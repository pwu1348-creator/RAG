from fastapi import APIRouter, Request
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
        creator_admin_id="system",
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
