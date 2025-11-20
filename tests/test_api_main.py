import pytest
from config import settings

@pytest.mark.asyncio
async def test_api_root(client):
    response = await client.get("/")
    assert response.status_code == 200

