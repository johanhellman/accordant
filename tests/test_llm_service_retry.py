from unittest.mock import AsyncMock

import httpx
import pytest

from backend.openrouter import query_model


@pytest.mark.asyncio
async def test_query_model_success(mocker):
    """Test successful query without retries."""
    mock_post = mocker.patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Success", "reasoning_details": None}}]
    }
    mock_post.return_value = mock_response

    result = await query_model(
        "test-model", [{"role": "user", "content": "hi"}], api_key="key", base_url="url"
    )

    assert result["content"] == "Success"
    assert mock_post.call_count == 1


@pytest.mark.asyncio
async def test_query_model_retry_429(mocker):
    """Test retry on 429 Too Many Requests."""
    mock_post = mocker.patch("httpx.AsyncClient.post", new_callable=AsyncMock)

    fail_response = mocker.Mock()
    fail_response.status_code = 429
    # Important: tenacity retries if _execute_request raises HTTPStatusError
    # which it does manually for 429
    fail_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Too Many Requests", request=mocker.Mock(), response=fail_response
    )

    success_response = mocker.Mock()
    success_response.status_code = 200
    success_response.json.return_value = {
        "choices": [{"message": {"content": "Success after retry", "reasoning_details": None}}]
    }
    success_response.raise_for_status = mocker.Mock()

    mock_post.side_effect = [fail_response, success_response]

    mocker.patch("asyncio.sleep", new_callable=AsyncMock)

    result = await query_model(
        "test-model", [{"role": "user", "content": "hi"}], api_key="key", base_url="url"
    )

    assert result["content"] == "Success after retry"
    assert mock_post.call_count == 2


@pytest.mark.asyncio
async def test_query_model_retry_500(mocker):
    """Test retry on 500 Server Error."""
    mock_post = mocker.patch("httpx.AsyncClient.post", new_callable=AsyncMock)

    fail_response = mocker.Mock()
    fail_response.status_code = 500
    fail_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server Error", request=mocker.Mock(), response=fail_response
    )

    success_response = mocker.Mock()
    success_response.status_code = 200
    success_response.json.return_value = {
        "choices": [{"message": {"content": "Success after 500", "reasoning_details": None}}]
    }
    success_response.raise_for_status = mocker.Mock()

    mock_post.side_effect = [fail_response, success_response]

    mocker.patch("asyncio.sleep", new_callable=AsyncMock)

    result = await query_model(
        "test-model", [{"role": "user", "content": "hi"}], api_key="key", base_url="url"
    )

    assert result["content"] == "Success after 500"
    assert mock_post.call_count == 2


@pytest.mark.asyncio
async def test_query_model_retry_timeout(mocker):
    """Test retry on Timeout."""
    mock_post = mocker.patch("httpx.AsyncClient.post", new_callable=AsyncMock)

    success_response = mocker.Mock()
    success_response.status_code = 200
    success_response.json.return_value = {
        "choices": [{"message": {"content": "Success after timeout", "reasoning_details": None}}]
    }
    success_response.raise_for_status = mocker.Mock()

    mock_post.side_effect = [httpx.ReadTimeout("Timeout"), success_response]

    mocker.patch("asyncio.sleep", new_callable=AsyncMock)

    result = await query_model(
        "test-model", [{"role": "user", "content": "hi"}], api_key="key", base_url="url"
    )

    assert result is not None
    assert result["content"] == "Success after timeout"
    assert mock_post.call_count == 2


@pytest.mark.asyncio
async def test_query_model_max_retries_fail(mocker):
    """Test failure after max retries."""
    mock_post = mocker.patch("httpx.AsyncClient.post", new_callable=AsyncMock)

    fail_response = mocker.Mock()
    fail_response.status_code = 500
    fail_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500", request=mocker.Mock(), response=fail_response
    )

    mock_post.return_value = fail_response

    mocker.patch("asyncio.sleep", new_callable=AsyncMock)

    from backend.config import LLM_MAX_RETRIES

    result = await query_model(
        "test-model", [{"role": "user", "content": "hi"}], api_key="key", base_url="url"
    )

    assert result is None
    assert mock_post.call_count == LLM_MAX_RETRIES


@pytest.mark.asyncio
async def test_query_model_non_retriable_error(mocker):
    """Test non-retriable error (e.g. 400 Bad Request)."""
    mock_post = mocker.patch("httpx.AsyncClient.post", new_callable=AsyncMock)

    fail_response = mocker.Mock()
    fail_response.status_code = 400
    fail_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "400", request=mocker.Mock(), response=fail_response
    )

    mock_post.return_value = fail_response

    mocker.patch("asyncio.sleep", new_callable=AsyncMock)

    result = await query_model(
        "test-model", [{"role": "user", "content": "hi"}], api_key="key", base_url="url"
    )

    assert result is None
    assert mock_post.call_count == 1
