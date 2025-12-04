"""Edge case tests for llm_service.py to improve coverage."""

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
async def test_get_available_models_missing_id_field(mock_httpx_client):
    """Test get_available_models skips models without id field."""
    with patch("backend.llm_service._MODELS_CACHE", {}):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "openai/gpt-4", "name": "GPT-4"},
                {"name": "Model without ID"},  # Missing id field
                {"id": "anthropic/claude-3", "name": "Claude 3"},
            ]
        }
        mock_httpx_client.get.return_value = mock_response

        models = await get_available_models("fake-key", "https://openrouter.ai/api/v1")

        # Should only include models with id field
        assert len(models) == 2
        assert models[0]["id"] == "openai/gpt-4"
        assert models[1]["id"] == "anthropic/claude-3"


@pytest.mark.asyncio
async def test_get_available_models_empty_data_array(mock_httpx_client):
    """Test get_available_models handles empty data array."""
    with patch("backend.llm_service._MODELS_CACHE", {}):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_httpx_client.get.return_value = mock_response

        models = await get_available_models("fake-key", "https://openrouter.ai/api/v1")

        assert models == []


@pytest.mark.asyncio
async def test_get_available_models_missing_data_key(mock_httpx_client):
    """Test get_available_models handles missing data key."""
    with patch("backend.llm_service._MODELS_CACHE", {}):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # No 'data' key
        mock_httpx_client.get.return_value = mock_response

        models = await get_available_models("fake-key", "https://openrouter.ai/api/v1")

        assert models == []


@pytest.mark.asyncio
async def test_get_available_models_provider_extraction():
    """Test get_available_models correctly extracts provider from model ID."""
    with patch("backend.llm_service._MODELS_CACHE", {}):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "openai/gpt-4", "name": "GPT-4"},
                {"id": "anthropic/claude-3", "name": "Claude 3"},
                {"id": "single-word-model", "name": "Single Word"},  # No slash
            ]
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response

            models = await get_available_models("fake-key", "https://openrouter.ai/api/v1")

            assert models[0]["provider"] == "openai"
            assert models[1]["provider"] == "anthropic"
            assert models[2]["provider"] == "unknown"  # No slash in ID


@pytest.mark.asyncio
async def test_get_available_models_name_fallback():
    """Test get_available_models uses model ID as name fallback."""
    with patch("backend.llm_service._MODELS_CACHE", {}):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "openai/gpt-4"},  # No name field
                {"id": "anthropic/claude-3", "name": "Claude 3"},
            ]
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response

            models = await get_available_models("fake-key", "https://openrouter.ai/api/v1")

            assert models[0]["name"] == "openai/gpt-4"  # Falls back to ID
            assert models[1]["name"] == "Claude 3"


@pytest.mark.asyncio
async def test_get_available_models_cache_per_base_url():
    """Test get_available_models caches separately per base_url."""
    base_url1 = "https://openrouter.ai/api/v1"
    base_url2 = "https://api.together.xyz/v1"

    cached_models1 = [{"id": "model1", "name": "Model 1", "provider": "test1"}]
    cached_models2 = [{"id": "model2", "name": "Model 2", "provider": "test2"}]
    cached_time = datetime.now()

    mock_cache = {
        base_url1: {"models": cached_models1, "timestamp": cached_time},
        base_url2: {"models": cached_models2, "timestamp": cached_time},
    }

    with patch("backend.llm_service._MODELS_CACHE", mock_cache):
        models1 = await get_available_models("fake-key", base_url1)
        models2 = await get_available_models("fake-key", base_url2)

        assert models1 == cached_models1
        assert models2 == cached_models2
        assert models1 != models2


@pytest.mark.asyncio
async def test_get_available_models_exception_handling(mock_httpx_client):
    """Test get_available_models handles exceptions gracefully."""
    with patch("backend.llm_service._MODELS_CACHE", {}):
        mock_httpx_client.get.side_effect = Exception("Network error")

        models = await get_available_models("fake-key", "https://openrouter.ai/api/v1")

        assert models == []


@pytest.mark.asyncio
async def test_get_available_models_generic_url_stripping():
    """Test get_available_models correctly strips /chat/completions from base URL."""
    with patch("backend.llm_service._MODELS_CACHE", {}):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "test-model"}]}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response

            # Base URL with /chat/completions
            await get_available_models(
                "fake-key", "https://api.example.com/v1/chat/completions"
            )

            # Verify URL was constructed correctly
            call_args = mock_client.get.call_args
            assert call_args[0][0] == "https://api.example.com/v1/models"


@pytest.mark.asyncio
async def test_get_available_models_cache_ttl_boundary():
    """Test get_available_models refreshes cache at TTL boundary."""
    base_url = "https://openrouter.ai/api/v1"
    cached_models = [{"id": "old-model"}]
    # Cache expires in 1 minute (just under TTL)
    cached_time = datetime.now() - timedelta(minutes=59)

    mock_cache = {base_url: {"models": cached_models, "timestamp": cached_time}}

    with patch("backend.llm_service._MODELS_CACHE", mock_cache):
        # Should use cache
        models = await get_available_models("fake-key", base_url)
        assert models == cached_models

    # Cache expired (just over TTL)
    cached_time_expired = datetime.now() - timedelta(minutes=61)
    mock_cache_expired = {base_url: {"models": cached_models, "timestamp": cached_time_expired}}

    with patch("backend.llm_service._MODELS_CACHE", mock_cache_expired):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "new-model"}]}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response

            models = await get_available_models("fake-key", base_url)

            # Should fetch new models
            assert models[0]["id"] == "new-model"
            mock_client.get.assert_called_once()

