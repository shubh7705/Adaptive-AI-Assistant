from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config.settings import settings
import os

# Fallback to SQLite for local development to ensure it's runnable out-of-the-box
# In production / Docker, this will be the PostgreSQL URL
db_url = settings.DATABASE_URL
if "postgresql" in db_url and not os.getenv("POSTGRES_READY"):
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

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
