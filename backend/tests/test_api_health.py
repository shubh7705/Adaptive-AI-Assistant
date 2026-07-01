import pytest

@pytest.mark.asyncio
async def test_health_check(client):
    """
    Tests that the FastAPI application is alive and responding.
    """
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "message": "ModelRouter AI API is running"}
