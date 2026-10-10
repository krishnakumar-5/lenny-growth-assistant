from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.sources import router as sources_router
from app.api.routes.chat import router as chat_router
from app.api.routes.skills import router as skills_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="", tags=["health"])
api_router.include_router(sources_router, prefix="", tags=["sources"])
api_router.include_router(chat_router, prefix="", tags=["chat"])
api_router.include_router(skills_router, prefix="", tags=["skills"])

__all__ = ["api_router"]
