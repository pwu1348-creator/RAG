from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .response import error_response
from .logger import logger


def register_error_handlers(app: FastAPI):
    @app.exception_handler(400)
    async def bad_request(request: Request, error: Exception):
        return error_response("Bad request", 400)
    
    @app.exception_handler(404)
    async def not_found(request: Request, error: Exception):
        return error_response("Not found", 404)
    
    @app.exception_handler(405)
    async def method_not_allowed(request: Request, error: Exception):
        return error_response("Method not allowed", 405)
    
    @app.exception_handler(413)
    async def request_entity_too_large(request: Request, error: Exception):
        return error_response("File too large", 413)
    
    @app.exception_handler(500)
    async def internal_server_error(request: Request, error: Exception):
        logger.error(f"Server error: {str(error)}")
        return error_response("Internal server error", 500)
    
    @app.exception_handler(Exception)
    async def handle_exception(request: Request, error: Exception):
        logger.exception(f"Unhandled exception: {str(error)}")
        return error_response(f"Server error: {str(error)}", 500)
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return error_response(exc.detail, exc.status_code)
