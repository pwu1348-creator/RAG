from .parser_routes import router as parser_router
from .auth_routes import router as auth_router
from .admin_routes import router as admin_router
from .kb_routes import router as kb_router
from .settings_routes import router as settings_router

__all__ = ['parser_router', 'auth_router', 'admin_router', 'kb_router', 'settings_router']
