import pytest
from unittest.mock import AsyncMock, patch
from utils.cache import cache

@pytest.mark.asyncio
async def test_cache_set_get():
    with patch.object(cache, "set", new=AsyncMock()) as mock_set:
        await cache.set("test_key", "value")
        mock_set.assert_awaited()

    with patch.object(cache, "get", new=AsyncMock(return_value="value")) as mock_get:
        v = await cache.get("test_key")
        assert v == "value"
