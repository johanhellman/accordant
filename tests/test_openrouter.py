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
        mock_response = {
            "choices": [{"message": {"content": "Test response", "reasoning_details": None}}]
        }

        with patch("backend.openrouter.get_semaphore") as mock_semaphore:
            mock_semaphore.return_value.__aenter__ = AsyncMock(return_value=None)
            mock_semaphore.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

                mock_response_obj = MagicMock()
                mock_response_obj.json.return_value = mock_response
                mock_response_obj.raise_for_status = MagicMock()
                mock_client.post.return_value = mock_response_obj

                result = await query_model(
                    "test-model",
                    [{"role": "user", "content": "Hello"}],
                    api_key="key",
                    base_url="url",
                )

                assert result is not None
                assert result["content"] == "Test response"

                # Verify API call was made correctly
                mock_client.post.assert_called_once()
                call_args = mock_client.post.call_args
                assert call_args[0][0] == "url"
                assert call_args[1]["json"]["model"] == "test-model"

    @pytest.mark.asyncio
    async def test_query_model_retry_on_429(self):
        """Test retry logic on 429 Too Many Requests."""
        mock_error = httpx.HTTPStatusError(
            "429 Too Many Requests", request=MagicMock(), response=MagicMock(status_code=429)
        )

        mock_success_response = {"choices": [{"message": {"content": "Success after retry"}}]}

        with patch("backend.openrouter.get_semaphore") as mock_semaphore:
            mock_semaphore.return_value.__aenter__ = AsyncMock(return_value=None)
            mock_semaphore.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

                mock_response_obj = MagicMock()
                mock_response_obj.json.return_value = mock_success_response
                mock_response_obj.raise_for_status = MagicMock()

                mock_client.post.side_effect = [mock_error, mock_response_obj]

                with patch("asyncio.sleep", new_callable=AsyncMock):
                    result = await query_model(
                        "test-model",
                        [{"role": "user", "content": "Hello"}],
                        api_key="key",
                        base_url="url",
                    )

                    assert result["content"] == "Success after retry"
                    assert mock_client.post.call_count == 2


class TestQueryModelsParallel:
    """Tests for query_models_parallel function."""

    @pytest.mark.asyncio
    async def test_query_models_parallel_success(self):
        """Test parallel querying of multiple models."""
        models = ["model1", "model2", "model3"]
        mock_responses = {
            "model1": {"content": "Response 1"},
            "model2": {"content": "Response 2"},
            "model3": {"content": "Response 3"},
        }

        async def mock_query_model(*args, **kwargs):
            # Extract model from args or kwargs
            # query_model(model, messages, ...)
            model = args[0] if args else kwargs.get("model")
            return mock_responses.get(model)

        with patch("backend.openrouter.query_model", side_effect=mock_query_model):
            result = await query_models_parallel(
                models, [{"role": "user", "content": "Hello"}], api_key="key", base_url="url"
            )

            assert len(result) == 3
            assert result["model1"]["content"] == "Response 1"
            assert result["model2"]["content"] == "Response 2"
            assert result["model3"]["content"] == "Response 3"

    @pytest.mark.asyncio
    async def test_query_models_parallel_partial_failure(self):
        """Test parallel querying when some models fail."""
        models = ["model1", "model2"]

        async def mock_query_model(*args, **kwargs):
            model = args[0] if args else kwargs.get("model")

            if model == "model2":
                return None
            return {"content": "Response 1"}

        with patch("backend.openrouter.query_model", side_effect=mock_query_model):
            result = await query_models_parallel(
                models, [{"role": "user", "content": "Hello"}], api_key="key", base_url="url"
            )

            assert result["model1"] is not None
            assert result["model2"] is None
