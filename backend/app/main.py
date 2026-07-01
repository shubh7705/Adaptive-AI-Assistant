from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from prometheus_fastapi_instrumentator import Instrumentator

from app.config.settings import settings
from app.api.api_v1 import api_router
from app.config.logger import setup_logging
from app.cache.semantic_cache import SemanticCacheManager

def create_app() -> FastAPI:
    # Initialize Loguru
    setup_logging()
    
    # Initialize Semantic Cache
    cache_manager = SemanticCacheManager()
    cache_manager.initialize_cache()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Intelligent Multi-Model AI Router API",
        openapi_url="/api/v1/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Instrument Prometheus Metrics
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

    # Configure CORS
    # In production, replace `allow_origins=["*"]` with specific frontend domains.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include the main API router
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/")
    async def root():
        return {
            "message": "Welcome to ModelRouter AI",
            "docs": "/docs",
            "health": "/api/v1/health"
        }

    return app

app = create_app()

if __name__ == "__main__":
    # Allows running this file directly for development
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
