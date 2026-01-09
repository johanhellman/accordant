"""Tests for OpenRouter API client integration."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from backend.openrouter import query_model, query_models_parallel


class TestQueryModel:
    """Tests for query_model function."""

    @pytest.mark.asyncio
    async def test_query_model_success(self):
        """Test successful model query."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response", "reasoning_details": None}}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_instance = AsyncMock()
            mock_client_class.return_value = mock_instance
            mock_instance.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response

            result = await query_model(
                "test-model",
                [{"role": "user", "content": "Hello"}],
                api_key="key",
                base_url="url",
            )

            assert result is not None
            assert result["content"] == "Test response"

    @pytest.mark.asyncio
    async def test_query_model_retry_on_429(self):
        """Test retry logic on 429 Too Many Requests."""
        mock_error = httpx.HTTPStatusError(
            "429 Too Many Requests", request=MagicMock(), response=MagicMock(status_code=429)
        )
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Success after retry"}}]
        }
        mock_response.raise_for_status = MagicMock()

        with (
            patch("httpx.AsyncClient") as mock_client_class,
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            mock_client = AsyncMock()
            mock_instance = AsyncMock()
            mock_client_class.return_value = mock_instance
            mock_instance.__aenter__.return_value = mock_client
            mock_client.post.side_effect = [mock_error, mock_response]

            result = await query_model(
                "test-model",
                [{"role": "user", "content": "Hello"}],
                api_key="key",
                base_url="url",
            )

            assert result is not None
            assert result["content"] == "Success after retry"
            assert mock_client.post.call_count == 2


class TestQueryModelsParallel:
    """Tests for query_models_parallel function."""

    @pytest.mark.asyncio
    async def test_query_models_parallel_success(self):
        """Test parallel querying of multiple models."""
        models = ["model1", "model2", "model3"]

        def mock_post(url, **kwargs):
            m = MagicMock()
            m.status_code = 200
            model = kwargs["json"]["model"]
            m.json.return_value = {"choices": [{"message": {"content": f"Response for {model}"}}]}
            m.raise_for_status = MagicMock()
            return m

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_instance = AsyncMock()
            mock_client_class.return_value = mock_instance
            mock_instance.__aenter__.return_value = mock_client
            mock_client.post.side_effect = mock_post

            result = await query_models_parallel(
                models, [{"role": "user", "content": "Hello"}], api_key="key", base_url="url"
            )

            assert len(result) == 3
            assert result["model1"]["content"] == "Response for model1"
            assert result["model2"]["content"] == "Response for model2"
            assert result["model3"]["content"] == "Response for model3"

    @pytest.mark.asyncio
    async def test_query_models_parallel_partial_failure(self):
        """Test parallel querying when some models fail."""
        models = ["model1", "model2"]

        def mock_post(url, **kwargs):
            model = kwargs["json"]["model"]
            if model == "model2":
                raise Exception("Network error")
            m = MagicMock()
            m.status_code = 200
            m.json.return_value = {"choices": [{"message": {"content": "Response 1"}}]}
            m.raise_for_status = MagicMock()
            return m

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_instance = AsyncMock()
            mock_client_class.return_value = mock_instance
            mock_instance.__aenter__.return_value = mock_client
            mock_client.post.side_effect = mock_post

            result = await query_models_parallel(
                models, [{"role": "user", "content": "Hello"}], api_key="key", base_url="url"
            )

            assert result["model1"] is not None
            assert result["model2"] is None
