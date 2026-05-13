
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config import config
from utils.logger import logger

router = APIRouter(tags=["用户认证"])

_PARSER_BASE = "http://localhost:8001/api/v1"


class UserLoginRequest(BaseModel):
    username: str
    password: str


@router.post("/auth/user/login")
async def user_login(body: UserLoginRequest):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{_PARSER_BASE}/auth/user/login",
                json={"username": body.username, "password": body.password},
            )
        return JSONResponse(status_code=resp.status_code, content=resp.json())
    except httpx.ConnectError:
        logger.error("[Auth] Parser Service 连接失败")
        return JSONResponse(
            status_code=503,
            content={"code": 503, "message": "认证服务暂时不可用，请稍后重试", "data": None},
        )
    except Exception as e:
        logger.error(f"[Auth] 用户登录代理失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "服务器内部错误", "data": None},
        )


@router.post("/auth/user/logout")
async def user_logout(request: Request):
    try:
        token = request.headers.get("Authorization", "")
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{_PARSER_BASE}/auth/logout",
                headers={"Authorization": token},
            )
        return JSONResponse(status_code=resp.status_code, content=resp.json())
    except Exception as e:
        logger.error(f"[Auth] 用户登出代理失败: {e}")
        return JSONResponse(
            status_code=200,
            content={"code": 200, "message": "已登出", "data": None},
        )


@router.get("/auth/user/info")
async def get_user_info(request: Request):
    try:
        token = request.headers.get("Authorization", "")
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{_PARSER_BASE}/auth/user/info",
                headers={"Authorization": token},
            )
        return JSONResponse(status_code=resp.status_code, content=resp.json())
    except httpx.ConnectError:
        logger.error("[Auth] Parser Service 连接失败")
        return JSONResponse(
            status_code=503,
            content={"code": 503, "message": "服务暂时不可用", "data": None},
        )
    except Exception as e:
        logger.error(f"[Auth] 获取用户信息代理失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "服务器内部错误", "data": None},
        )


class UpdateProfileRequest(BaseModel):
    username: str = None
    old_password: str = None
    password: str = None


@router.put("/auth/user/info")
async def update_user_info(request: Request, body: UpdateProfileRequest):
    try:
        token = request.headers.get("Authorization", "")
        payload = {}
        if body.username:
            payload["username"] = body.username
        if body.old_password:
            payload["old_password"] = body.old_password
        if body.password:
            payload["password"] = body.password
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.put(
                f"{_PARSER_BASE}/auth/user/info",
                json=payload,
                headers={"Authorization": token},
            )
        return JSONResponse(status_code=resp.status_code, content=resp.json())
    except httpx.ConnectError:
        logger.error("[Auth] Parser Service 连接失败")
        return JSONResponse(
            status_code=503,
            content={"code": 503, "message": "服务暂时不可用", "data": None},
        )
    except Exception as e:
        logger.error(f"[Auth] 修改用户信息代理失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "服务器内部错误", "data": None},
        )


@router.post("/auth/user/avatar")
async def upload_user_avatar(request: Request):
    try:
        token = request.headers.get("Authorization", "")
        content_type = request.headers.get("Content-Type", "")
        body = await request.body()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{_PARSER_BASE}/auth/user/avatar",
                content=body,
                headers={
                    "Authorization": token,
                    "Content-Type": content_type,
                },
            )
        return JSONResponse(status_code=resp.status_code, content=resp.json())
    except httpx.ConnectError:
        logger.error("[Auth] Parser Service 连接失败")
        return JSONResponse(
            status_code=503,
            content={"code": 503, "message": "服务暂时不可用", "data": None},
        )
    except Exception as e:
        logger.error(f"[Auth] 上传头像代理失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "服务器内部错误", "data": None},
        )
