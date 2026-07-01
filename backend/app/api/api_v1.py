from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.registry import router as registry_router
from app.api.analytics import router as analytics_router
from app.api.chat import router as chat_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(registry_router, prefix="/registry", tags=["registry"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])

@api_router.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint to verify the API is up and running.
    """
    return {"status": "ok", "message": "ModelRouter API is healthy"}
