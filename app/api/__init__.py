from fastapi import APIRouter
from app.api.routes_health import router as health_router
from app.api.routes_auth import router as auth_router
from app.api.routes_documents import router as documents_router
from app.api.routes_chat import router as chat_router
from app.api.routes_agents import router as agents_router
from app.api.routes_analysis import router as analysis_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["Health"])
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(auth_router, prefix="/user", tags=["User Profile"])
api_router.include_router(documents_router, tags=["Documents"])
api_router.include_router(chat_router, tags=["Chat"])
api_router.include_router(agents_router, tags=["Agents"])
api_router.include_router(analysis_router, tags=["Analysis & Intelligence"])

__all__ = ["api_router"]
