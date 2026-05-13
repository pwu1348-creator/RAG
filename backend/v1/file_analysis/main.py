import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_path, override=False)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config import config
from routes import parser_router, auth_router, admin_router, kb_router, settings_router
from utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Service starting...")
    yield
    logger.info("Service shutting down...")


def create_app() -> FastAPI:
    app = FastAPI(
        title="File Analysis Service",
        description="文档解析与向量存储服务",
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

    app.include_router(parser_router, prefix=f"{config.api.API_PREFIX}/parser")
    app.include_router(auth_router, prefix=f"{config.api.API_PREFIX}/auth")
    app.include_router(admin_router, prefix=f"{config.api.API_PREFIX}/admin")
    app.include_router(kb_router, prefix=f"{config.api.API_PREFIX}/knowledge-bases")
    app.include_router(settings_router, prefix=f"{config.api.API_PREFIX}/settings")

    _uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
    os.makedirs(_uploads_dir, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=_uploads_dir), name="uploads")

    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": "file-analysis",
            "version": "1.0.0"
        }

    @app.get("/")
    async def index():
        return {
            "service": "File Analysis Service",
            "version": "1.0.0",
            "port": 8001,
            "docs": "/docs"
        }

    return app


def main():
    import uvicorn

    print(f"""
╔══════════════════════════════════════════════════════════╗
║           File Analysis Service (Port 8001)              ║
╠══════════════════════════════════════════════════════════╣
║  服务地址: http://{config.api.HOST}:8001                  ║
║  API文档: http://{config.api.HOST}:8001/docs              ║
║  API前缀: {config.api.API_PREFIX}                         ║
║  调试模式: {'开启' if config.api.DEBUG else '关闭'}         ║
╚══════════════════════════════════════════════════════════╝
""")

    uvicorn.run(
        "main:create_app",
        host=config.api.HOST,
        port=8001,
        reload=config.api.DEBUG,
        factory=True,
    )


if __name__ == "__main__":
    main()
