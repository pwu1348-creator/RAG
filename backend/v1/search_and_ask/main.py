"""
Search & Ask Service 入口

检索与问答微服务 (Port 8002)

启动方式:
    cd backend/v1/search_and_ask
    python main.py
"""

import os
import sys
from contextlib import asynccontextmanager

_SEARCH_AND_ASK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SEARCH_AND_ASK)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import config
from routes import router as search_router
from routes.auth_routes import router as auth_router
from utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Search & Ask Service v2.0 starting...")
    yield
    logger.info("Search & Ask Service shutting down...")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Search & Ask Service",
        description="检索与问答服务",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.api.CORS_ORIGINS,
        allow_credentials=config.api.CORS_ALLOW_CREDENTIALS,
        allow_methods=config.api.CORS_ALLOW_METHODS,
        allow_headers=config.api.CORS_ALLOW_HEADERS,
    )

    # auth 路由挂在 /api/v1 下，不加 /search 前缀
    app.include_router(auth_router, prefix=config.api.API_PREFIX)
    # 检索/问答/索引路由挂在 /api/v1/search 下
    app.include_router(search_router, prefix=f"{config.api.API_PREFIX}/search")

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "search-and-ask", "version": "2.0.0"}

    @app.get("/")
    async def index():
        return {"service": "Search & Ask Service", "version": "2.0.0", "port": config.api.PORT, "docs": "/docs"}

    return app


def main():
    import uvicorn
    print(f"\n  Search & Ask Service v2.0 on http://{config.api.HOST}:{config.api.PORT}\n")
    uvicorn.run("main:create_app", host=config.api.HOST, port=config.api.PORT, reload=config.api.DEBUG, factory=True)


if __name__ == "__main__":
    main()
