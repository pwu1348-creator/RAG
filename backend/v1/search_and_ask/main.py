import os
import sys
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import config
from routes import router
from utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Search and Ask Service starting...")
    yield
    logger.info("Search and Ask Service shutting down...")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Search and Ask Service",
        description="检索与问答服务",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.api.CORS_ORIGINS,
        allow_credentials=config.api.CORS_ALLOW_CREDENTIALS,
        allow_methods=config.api.CORS_ALLOW_METHODS,
        allow_headers=config.api.CORS_ALLOW_HEADERS,
    )

    app.include_router(router, prefix=f"{config.api.API_PREFIX}/search")

    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": "search-and-ask",
            "version": "1.0.0"
        }

    @app.get("/")
    async def index():
        return {
            "service": "Search and Ask Service",
            "version": "1.0.0",
            "port": 8002,
            "docs": "/docs"
        }

    return app


def main():
    import uvicorn

    print(f"""
╔══════════════════════════════════════════════════════════╗
║         Search and Ask Service (Port 8002)               ║
╠══════════════════════════════════════════════════════════╣
║  服务地址: http://{config.api.HOST}:8002                  ║
║  API文档: http://{config.api.HOST}:8002/docs              ║
║  API前缀: {config.api.API_PREFIX}                         ║
║  调试模式: {'开启' if config.api.DEBUG else '关闭'}         ║
╚══════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "main:create_app",
        host=config.api.HOST,
        port=8002,
        reload=config.api.DEBUG,
        factory=True
    )


if __name__ == "__main__":
    main()
