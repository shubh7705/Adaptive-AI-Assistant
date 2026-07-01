import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import create_app

@pytest.fixture(scope="session")
def app():
    """
    Returns the FastAPI app instance for testing.
    """
    # Overwrite DB URLs or disable caches here for testing if needed
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
