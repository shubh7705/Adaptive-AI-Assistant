import pytest

@pytest.mark.asyncio
async def test_registry_public_get_allowed(client):
    response = await client.get("/api/v1/registry/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_auth_routes_removed(client):
    response = await client.post("/api/v1/auth/login", data={"username": "test@example.com", "password": "password"})
    assert response.status_code == 404

