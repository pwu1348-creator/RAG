"""
用户认证路由 — 代理转发给 Parser Service

用户登录必须经过 QA Service (8002)，
QA Service 不启动则用户无法登录。
"""

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config import config
from utils.logger import logger

router = APIRouter(tags=["用户认证"])

# Parser Service 地址（用户认证由它负责）
_PARSER_BASE = "http://localhost:8001/api/v1"


class UserLoginRequest(BaseModel):
    username: str
    password: str


@router.post("/auth/user/login")
async def user_login(body: UserLoginRequest):
    """
    用户登录入口（代理到 Parser Service）。
    QA Service 未启动时此接口不可用，用户无法登录。
    """
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
    """用户登出（代理到 Parser Service）"""
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
