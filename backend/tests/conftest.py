import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import create_app
from app.database.session import engine
from app.database.base import Base
import app.models.registry  # noqa: F401
import app.models.chat      # noqa: F401
import app.models.user      # noqa: F401
import app.models.analytics # noqa: F401

@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_test_db():
    """
    Ensure all SQLAlchemy models are registered and tables created for tests.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

@pytest.fixture(scope="session")
def app():
    """
    Returns the FastAPI app instance for testing.
    """
    return create_app()

@pytest_asyncio.fixture(scope="function")
async def client(app):
    """
    Returns an async HTTP client for endpoint testing.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver"
    ) as ac:
        yield ac

