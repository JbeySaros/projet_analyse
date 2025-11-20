import pytest

@pytest.mark.asyncio
async def test_api_root(client):
    response = await client.get("/")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_docs_accessible(client):
    response = await client.get("/docs")
    assert response.status_code == 200
