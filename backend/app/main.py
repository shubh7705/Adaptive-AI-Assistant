from contextlib import asynccontextmanager
from app.database.session import engine
from app.database.base import Base
import asyncio

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

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Import models so they are registered with Base
        from app.models.registry import ModelRegistry
        from app.models.chat import Conversation, Message
        from app.models.user import User
        from app.models.analytics import RoutingLog, ModelBenchmarks, ModelMetrics
        
        from sqlalchemy.future import select
        from sqlalchemy import delete
        from app.database.session import AsyncSessionLocal
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        # Seed the database with default and free models
        async with AsyncSessionLocal() as session:
            # Purge removed models if they exist in the DB
            removed_model_names = [
                "llama-3.3-70b-versatile",
                "openai/gpt-oss-120b:free",
                "google/gemma-4-31b-it:free",
                "llama-3.1-8b-instant",
                "qwen/qwen3.6-27b",
                "moonshotai/kimi-k2.6:free",
                "nvidia/nemotron-3.5-lightning:free",
            ]
            removed_model_ids = [
                "seed-llama-3-3-70b-groq",
                "seed-gpt-oss-120b-openrouter",
                "seed-gemma-4-31b-openrouter",
                "seed-llama3-1-8b-groq",
                "seed-qwen-3-6-27b-openrouter",
                "seed-kimi-k2-6-openrouter",
                "seed-nemotron-3-5-lightning-openrouter",
            ]
            await session.execute(
                delete(ModelRegistry).where(
                    (ModelRegistry.id.in_(removed_model_ids)) | (ModelRegistry.name.in_(removed_model_names))
                )
            )
            await session.flush()

            result = await session.execute(select(ModelRegistry.id))
            existing_ids = {row for row in result.scalars().all()}
            
            result_names = await session.execute(select(ModelRegistry.name))
            existing_names = {row for row in result_names.scalars().all()}
            
            models_to_seed = [
                ModelRegistry(
                    id="seed-gemini",
                    name="gemini-2.5-flash",
                    provider="google",
                    description="Fast, cheap Google model for general queries.",
                    cost_per_1k_tokens=0.00015,
                    supports_streaming=True,
                    supports_tools=True,
                    is_active=True
                ),
                ModelRegistry(
                    id="seed-deepseek",
                    name="deepseek/deepseek-chat",
                    provider="openrouter",
                    description="Powerful reasoning model for complex tasks.",
                    cost_per_1k_tokens=0.00028,
                    supports_streaming=True,
                    supports_tools=True,
                    is_active=True
                ),
                ModelRegistry(
                    id="seed-nemotron-3-openrouter",
                    name="nvidia/nemotron-3-super-120b-a12b:free",
                    provider="openrouter",
                    description="NVIDIA Nemotron 3 Super for orchestration and complex multi-agent tasks.",
                    cost_per_1k_tokens=0.00080,
                    supports_streaming=True,
                    supports_tools=True,
                    is_active=True
                ),
                ModelRegistry(
                    id="seed-ling-3-0-flash-vl-openrouter",
                    name="inclusionai/ling-3.0-flash-vl:free",
                    provider="openrouter",
                    description="InclusionAI Ling 3.0 Flash VL multimodal vision-language free model.",
                    cost_per_1k_tokens=0.0,
                    supports_streaming=True,
                    supports_vision=True,
                    supports_tools=True,
                    is_active=True
                ),
                ModelRegistry(
                    id="seed-laguna-s-2-1-openrouter",
                    name="poolside/laguna-s-2.1:free",
                    provider="openrouter",
                    description="Poolside Laguna S 2.1 advanced coding and reasoning free model.",
                    cost_per_1k_tokens=0.0,
                    supports_streaming=True,
                    supports_vision=False,
                    supports_tools=True,
                    is_active=True
                ),
                ModelRegistry(
                    id="seed-ling-3-0-flash-fin-openrouter",
                    name="inclusionai/ling-3.0-flash-fin:free",
                    provider="openrouter",
                    description="InclusionAI Ling 3.0 Flash Fin financial and analytical domain free model.",
                    cost_per_1k_tokens=0.0,
                    supports_streaming=True,
                    supports_vision=False,
                    supports_tools=True,
                    is_active=True
                )
            ]
            
            for m in models_to_seed:
                if m.id not in existing_ids and m.name not in existing_names:
                    session.add(m)
                    await session.flush()
                    
                    # Seed default benchmarks and metrics for new models
                    session.add(ModelBenchmarks(model_id=m.id))
                    session.add(ModelMetrics(model_id=m.id))
            
            # Backfill existing models with benchmarks/metrics and non-zero pricing if needed
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

        # Preload Intent Classifier to eliminate first-request cold-start latency
        try:
            from app.agents.intent.agent import IntentAgent
            IntentAgent()
        except Exception as e:
            logger.warning(f"Could not preload IntentAgent in lifespan: {e}")

        # Start the async outcome consumer background task.
        # It reads from Redis Streams and updates MetricsService + HistoryService
        # asynchronously, fully decoupled from the request path.
        from app.events.outcome_consumer import start_outcome_consumer
        consumer_task = asyncio.create_task(start_outcome_consumer())

        yield

        # Graceful shutdown: cancel the consumer task
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass

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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
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
