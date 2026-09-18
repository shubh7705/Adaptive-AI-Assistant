from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config.settings import settings
import os
import logging

logger = logging.getLogger(__name__)

db_url = settings.DATABASE_URL
if "postgresql" in db_url and not os.getenv("POSTGRES_READY"):
    logger.warning(
        "POSTGRES_READY env var not set. Falling back to SQLite for local development. "
        "Set POSTGRES_READY=true in your environment or docker-compose.yml for PostgreSQL."
    )
    db_url = "sqlite+aiosqlite:///./modelrouter.db"
    
engine = create_async_engine(
    db_url,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False} if "sqlite" in db_url else {}
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

from typing import AsyncGenerator

async def get_db() -> AsyncGenerator:
    async with AsyncSessionLocal() as session:
        yield session
