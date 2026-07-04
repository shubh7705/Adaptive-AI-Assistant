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

    from contextlib import asynccontextmanager
    from app.database.session import engine
    from app.database.base import Base

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Import models so they are registered with Base
        from app.models.registry import ModelRegistry
        from app.models.chat import Conversation, Message
        from app.models.analytics import RoutingLog, ModelBenchmarks, ModelMetrics
        
        from sqlalchemy.future import select
        from app.database.session import AsyncSessionLocal
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        # Seed the database with default and free models
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(ModelRegistry.id))
            existing_ids = {row for row in result.scalars().all()}
            
            models_to_seed = [
                ModelRegistry(
                    id="seed-gemini",
                    name="gemini-2.5-flash",
                    provider="google",
                    description="Fast, cheap Google model for general queries.",
                    cost_per_1k_tokens=0.0001,
                    supports_streaming=True,
                    supports_tools=True,
                    is_active=True
                ),
                ModelRegistry(
                    id="seed-deepseek",
                    name="deepseek/deepseek-chat",
                    provider="openrouter",
                    description="Powerful reasoning model for complex tasks.",
                    cost_per_1k_tokens=0.02,
                    supports_streaming=True,
                    supports_tools=True,
                    is_active=True
                ),

                ModelRegistry(
                    id="seed-llama3-1-8b-groq",
                    name="llama-3.1-8b-instant",
                    provider="groq",
                    description="Groq's highly efficient Llama 3.1 8B Instant model.",
                    cost_per_1k_tokens=0.0,
                    supports_streaming=True,
                    supports_tools=True,
                    is_active=True
                ),
                ModelRegistry(
                    id="seed-llama-3-3-70b-groq",
                    name="llama-3.3-70b-versatile",
                    provider="groq",
                    description="Highly versatile 70B model with blazing fast latency (~300 tk/s) on Groq.",
                    cost_per_1k_tokens=0.0,
                    supports_streaming=True,
                    supports_tools=True,
                    is_active=True
                ),
                ModelRegistry(
                    id="seed-qwen-3-6-27b-openrouter",
                    name="qwen/qwen3.6-27b",
                    provider="openrouter",
                    description="Qwen 3.6 27B model offering advanced reasoning on OpenRouter.",
                    cost_per_1k_tokens=0.0,
                    supports_streaming=True,
                    supports_tools=True,
                    is_active=True
                ),
                ModelRegistry(
                    id="seed-gpt-oss-120b-openrouter",
                    name="openai/gpt-oss-120b:free",
                    provider="openrouter",
                    description="OpenAI's massive 120B open-weight MoE model for advanced reasoning.",
                    cost_per_1k_tokens=0.0,
                    supports_streaming=True,
                    supports_tools=True,
                    is_active=True
                ),
                ModelRegistry(
                    id="seed-gemma-4-31b-openrouter",
                    name="google/gemma-4-31b-it:free",
                    provider="openrouter",
                    description="Google's Gemma 4 31B multimodal and coding powerhouse.",
                    cost_per_1k_tokens=0.0,
                    supports_streaming=True,
                    supports_tools=True,
                    is_active=True
                ),
                ModelRegistry(
                    id="seed-nemotron-3-openrouter",
                    name="nvidia/nemotron-3-super-120b-a12b:free",
                    provider="openrouter",
                    description="NVIDIA Nemotron 3 Super for orchestration and complex multi-agent tasks.",
                    cost_per_1k_tokens=0.0,
                    supports_streaming=True,
                    supports_tools=True,
                    is_active=True
                )
            ]
            
            for m in models_to_seed:
                if m.id not in existing_ids:
                    session.add(m)
                    await session.flush()
                    
                    # Seed default benchmarks and metrics for new models
                    session.add(ModelBenchmarks(model_id=m.id))
                    session.add(ModelMetrics(model_id=m.id))
            
            # Backfill existing models with benchmarks/metrics if they lack them
            result = await session.execute(select(ModelBenchmarks.model_id))
            existing_benchmark_ids = set(result.scalars().all())
            
            result = await session.execute(select(ModelMetrics.model_id))
            existing_metric_ids = set(result.scalars().all())
            
            for m_id in existing_ids:
                if m_id not in existing_benchmark_ids:
                    session.add(ModelBenchmarks(model_id=m_id))
                if m_id not in existing_metric_ids:
                    session.add(ModelMetrics(model_id=m_id))
                    
            await session.commit()
                
        yield

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Intelligent Multi-Model AI Router API",
        openapi_url="/api/v1/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    # Instrument Prometheus Metrics
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

    # Configure CORS
    # In production, replace `allow_origins=["*"]` with specific frontend domains.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
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
