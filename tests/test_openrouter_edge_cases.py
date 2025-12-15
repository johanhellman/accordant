"""Edge case tests for openrouter.py to improve coverage."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from backend.openrouter import get_semaphore, query_model, query_models_parallel


@pytest.mark.asyncio
async def test_query_model_timeout_retry():
    """Test query_model retries on timeout."""
    model = "test-model"
    messages = [{"role": "user", "content": "Hello"}]
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    mock_success_response = {"choices": [{"message": {"content": "Success after timeout"}}]}

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

            # First call times out, second succeeds
            mock_client.post.side_effect = [
                httpx.TimeoutException("Request timed out"),
                mock_response_obj,
            ]

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await query_model(model, messages, api_key=api_key, base_url=base_url)

                assert result["content"] == "Success after timeout"
                assert mock_client.post.call_count == 2


@pytest.mark.asyncio
async def test_query_model_5xx_retry():
    """Test query_model retries on 5xx server errors."""
    model = "test-model"
    messages = [{"role": "user", "content": "Hello"}]
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    mock_error = httpx.HTTPStatusError(
        "500 Internal Server Error", request=MagicMock(), response=MagicMock(status_code=500)
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
                result = await query_model(model, messages, api_key=api_key, base_url=base_url)

                assert result["content"] == "Success after retry"
                assert mock_client.post.call_count == 2


@pytest.mark.asyncio
async def test_query_model_max_retries_exceeded():
    """Test query_model returns None after max retries."""
    model = "test-model"
    messages = [{"role": "user", "content": "Hello"}]
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    mock_error = httpx.HTTPStatusError(
        "500 Internal Server Error", request=MagicMock(), response=MagicMock(status_code=500)
    )

    with patch("backend.openrouter.get_semaphore") as mock_semaphore:
        mock_semaphore.return_value.__aenter__ = AsyncMock(return_value=None)
        mock_semaphore.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            # Always raise error
            mock_client.post.side_effect = mock_error

            with (
                patch("backend.openrouter.LLM_MAX_RETRIES", 3),
                patch("asyncio.sleep", new_callable=AsyncMock),
            ):
                result = await query_model(model, messages, api_key=api_key, base_url=base_url)

                assert result is None
                assert mock_client.post.call_count == 3  # Max retries


@pytest.mark.asyncio
async def test_query_model_non_retryable_error():
    """Test query_model doesn't retry on non-retryable errors (4xx)."""
    model = "test-model"
    messages = [{"role": "user", "content": "Hello"}]
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    mock_error = httpx.HTTPStatusError(
        "400 Bad Request", request=MagicMock(), response=MagicMock(status_code=400)
    )

    with patch("backend.openrouter.get_semaphore") as mock_semaphore:
        mock_semaphore.return_value.__aenter__ = AsyncMock(return_value=None)
        mock_semaphore.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_client.post.side_effect = mock_error

            result = await query_model(model, messages, api_key=api_key, base_url=base_url)

            assert result is None
            assert mock_client.post.call_count == 1  # No retries for 4xx


@pytest.mark.asyncio
async def test_query_model_generic_exception():
    """Test query_model handles generic exceptions."""
    model = "test-model"
    messages = [{"role": "user", "content": "Hello"}]
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    with patch("backend.openrouter.get_semaphore") as mock_semaphore:
        mock_semaphore.return_value.__aenter__ = AsyncMock(return_value=None)
        mock_semaphore.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_client.post.side_effect = Exception("Unexpected error")

            result = await query_model(model, messages, api_key=api_key, base_url=base_url)

            assert result is None
            assert mock_client.post.call_count == 1


@pytest.mark.asyncio
async def test_query_model_with_temperature():
    """Test query_model includes temperature in payload when provided."""
    model = "test-model"
    messages = [{"role": "user", "content": "Hello"}]
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"
    temperature = 0.7

    mock_response = {"choices": [{"message": {"content": "Response"}}]}

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

            await query_model(
                model, messages, api_key=api_key, base_url=base_url, temperature=temperature
            )

            # Verify temperature was included in payload
            call_args = mock_client.post.call_args
            payload = call_args[1]["json"]
            assert payload["temperature"] == temperature


@pytest.mark.asyncio
async def test_query_model_without_temperature():
    """Test query_model doesn't include temperature when None."""
    model = "test-model"
    messages = [{"role": "user", "content": "Hello"}]
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    mock_response = {"choices": [{"message": {"content": "Response"}}]}

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

            await query_model(model, messages, api_key=api_key, base_url=base_url)

            # Verify temperature was not included in payload
            call_args = mock_client.post.call_args
            payload = call_args[1]["json"]
            assert "temperature" not in payload


@pytest.mark.asyncio
async def test_query_model_reasoning_details():
    """Test query_model includes reasoning_details when present."""
    model = "test-model"
    messages = [{"role": "user", "content": "Hello"}]
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    mock_response = {
        "choices": [
            {
                "message": {
                    "content": "Response",
                    "reasoning_details": {"reasoning": "Step by step reasoning"},
                }
            }
        ]
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

            result = await query_model(model, messages, api_key=api_key, base_url=base_url)

            assert result["content"] == "Response"
            assert result["reasoning_details"] == {"reasoning": "Step by step reasoning"}


@pytest.mark.asyncio
async def test_query_models_parallel_all_success():
    """Test query_models_parallel with all models succeeding."""
    models = ["model1", "model2", "model3"]
    messages = [{"role": "user", "content": "Hello"}]
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    async def mock_query_model(*args, **kwargs):
        model = args[0]
        return {"content": f"Response from {model}"}

    with patch("backend.openrouter.query_model", side_effect=mock_query_model):
        result = await query_models_parallel(models, messages, api_key=api_key, base_url=base_url)

        assert len(result) == 3
        assert result["model1"]["content"] == "Response from model1"
        assert result["model2"]["content"] == "Response from model2"
        assert result["model3"]["content"] == "Response from model3"


@pytest.mark.asyncio
async def test_query_models_parallel_all_fail():
    """Test query_models_parallel with all models failing."""
    models = ["model1", "model2"]
    messages = [{"role": "user", "content": "Hello"}]
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    async def mock_query_model(*args, **kwargs):
        return None

    with patch("backend.openrouter.query_model", side_effect=mock_query_model):
        result = await query_models_parallel(models, messages, api_key=api_key, base_url=base_url)

        assert len(result) == 2
        assert result["model1"] is None
        assert result["model2"] is None


@pytest.mark.asyncio
async def test_query_models_parallel_mixed_results():
    """Test query_models_parallel with mixed success/failure."""
    models = ["model1", "model2", "model3"]
    messages = [{"role": "user", "content": "Hello"}]
    api_key = "test-key"
    base_url = "https://api.test.com/v1/chat/completions"

    async def mock_query_model(*args, **kwargs):
        model = args[0]
        if model == "model2":
            return None
        return {"content": f"Response from {model}"}

    with patch("backend.openrouter.query_model", side_effect=mock_query_model):
        result = await query_models_parallel(models, messages, api_key=api_key, base_url=base_url)

        assert len(result) == 3
        assert result["model1"]["content"] == "Response from model1"
        assert result["model2"] is None
        assert result["model3"]["content"] == "Response from model3"


def test_get_semaphore_creates_once():
    """Test get_semaphore creates semaphore only once."""
    # Reset the global semaphore
    import backend.openrouter

    backend.openrouter._SEMAPHORE = None

    semaphore1 = get_semaphore()
    semaphore2 = get_semaphore()

    # Should return the same instance
    assert semaphore1 is semaphore2
