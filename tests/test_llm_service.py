from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from backend.llm_service import get_available_models


@pytest.fixture
def mock_httpx_client():
    with patch("httpx.AsyncClient", autospec=True) as mock_client:
        mock_context = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_context
        yield mock_context


@pytest.mark.asyncio
async def test_get_available_models_openrouter(mock_httpx_client):
    """Test fetching models from OpenRouter."""
    # Reset cache
    with patch("backend.llm_service._MODELS_CACHE", {}):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "openai/gpt-4", "name": "GPT-4"},
                {"id": "anthropic/claude-2", "name": "Claude 2"},
            ]
        }
        mock_httpx_client.get.return_value = mock_response

        models = await get_available_models("fake-key", "https://openrouter.ai/api/v1")

        assert len(models) == 2
        assert models[0]["id"] == "openai/gpt-4"
        assert models[0]["provider"] == "openai"
        assert models[1]["id"] == "anthropic/claude-2"
        assert models[1]["provider"] == "anthropic"

        # Verify URL
        mock_httpx_client.get.assert_called_with(
            "https://openrouter.ai/api/v1/models", headers={"Authorization": "Bearer fake-key"}
        )


@pytest.mark.asyncio
async def test_get_available_models_generic(mock_httpx_client):
    """Test fetching models from a generic OpenAI-compatible provider."""
    with patch("backend.llm_service._MODELS_CACHE", {}):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "llama-2-70b", "object": "model"}]}
        mock_httpx_client.get.return_value = mock_response

        # Base URL usually ends in /v1 or /v1/chat/completions
        models = await get_available_models(
            "fake-key", "https://api.together.xyz/v1/chat/completions"
        )

        assert len(models) == 1
        assert models[0]["id"] == "llama-2-70b"
        assert models[0]["provider"] == "unknown"  # Fallback when no slash

        # Verify URL construction: strips /chat/completions and adds /models
        mock_httpx_client.get.assert_called_with(
            "https://api.together.xyz/v1/models", headers={"Authorization": "Bearer fake-key"}
        )


@pytest.mark.asyncio
async def test_get_available_models_error(mock_httpx_client):
    """Test error handling when fetching models."""
    with patch("backend.llm_service._MODELS_CACHE", {}):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error", request=None, response=mock_response
        )

        mock_httpx_client.get.return_value = mock_response

        models = await get_available_models("fake-key", "https://openrouter.ai/api/v1")

        assert models == []


@pytest.mark.asyncio
async def test_get_available_models_caching(mock_httpx_client):
    """Test that caching works."""
    # Pre-populate cache
    base_url = "https://openrouter.ai/api/v1"
    cached_models = [{"id": "cached-model", "name": "Cached", "provider": "test"}]
    cached_time = datetime.now()

    # Mock the cache structure correctly: { base_url: { "models": [...], "timestamp": ... } }
    mock_cache = {base_url: {"models": cached_models, "timestamp": cached_time}}

    with patch("backend.llm_service._MODELS_CACHE", mock_cache):
        models = await get_available_models("fake-key", base_url)

        assert models == cached_models
        mock_httpx_client.get.assert_not_called()


@pytest.mark.asyncio
async def test_get_available_models_cache_expiry(mock_httpx_client):
    """Test that cache expires."""
    base_url = "https://openrouter.ai/api/v1"
    # Expired cache
    cached_models = [{"id": "old-model"}]
    cached_time = datetime.now() - timedelta(hours=2)

    mock_cache = {base_url: {"models": cached_models, "timestamp": cached_time}}

    with patch("backend.llm_service._MODELS_CACHE", mock_cache):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "new-model"}]}
        mock_httpx_client.get.return_value = mock_response

        models = await get_available_models("fake-key", base_url)

        assert len(models) == 1
        assert models[0]["id"] == "new-model"
        mock_httpx_client.get.assert_called_once()
