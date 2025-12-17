from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from backend.limiter import limiter
from backend.main import app
from backend.openrouter import query_model


@pytest.fixture
def enable_rate_limiter():
    """Temporarily enable rate limiter for these tests."""
    original = limiter.enabled
    limiter.enabled = True
    yield
    limiter.enabled = original


@pytest.mark.asyncio
async def test_openrouter_retry_logic():
    """Test standard exponential backoff retry logic."""
    model = "openai/gpt-4o"
    messages = [{"role": "user", "content": "hello"}]
    api_key = "test-key"
    base_url = "https://openrouter.ai/api/v1/chat/completions"

    # Create dummy request for raise_for_status compatibility
    dummy_request = httpx.Request("POST", base_url)

    # Mock response to fail twice with 500, then succeed
    r1 = httpx.Response(500, request=dummy_request)
    r2 = httpx.Response(503, request=dummy_request)
    r3 = httpx.Response(
        200,
        json={"choices": [{"message": {"content": "Success", "reasoning_details": None}}]},
        request=dummy_request,
    )

    mock_responses = [r1, r2, r3]

    # Explicitly use AsyncMock and ensure side_effect returns awaitables?
    # Actually AsyncMock wraps return values in futures automatically.
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = mock_responses

        # Patch sleep to speed up test
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await query_model(model, messages, api_key, base_url)

            # If result is None, the test will fail here with TypeError
            assert result is not None, "query_model returned None"
            assert result["content"] == "Success"
            assert mock_post.call_count == 3  # Initial + 2 failures
            assert mock_sleep.call_count == 2  # 2 sleeps


@pytest.mark.asyncio
async def test_openrouter_429_retry():
    """Test retry on 429 Too Many Requests."""
    model = "openai/gpt-4o"
    messages = [{"role": "user", "content": "hello"}]

    dummy_request = httpx.Request("POST", "https://api.example.com")

    # Needs 2 responses: 429 then 200
    mock_responses = [
        httpx.Response(429, request=dummy_request),
        httpx.Response(
            200,
            json={"choices": [{"message": {"content": "After 429", "reasoning_details": None}}]},
            request=dummy_request,
        ),
    ]

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = mock_responses
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await query_model(model, messages, "k", "u")
            assert result is not None
            assert result["content"] == "After 429"
            assert mock_post.call_count == 2


def test_rate_limiting_login(client, enable_rate_limiter):
    """Verify login rate limit (5/minute) triggers 429."""

    # Hit login 5 times (allowed)
    for _ in range(5):
        response = client.post(
            "/api/auth/token",
            data={"username": "test", "password": "password"},
            headers={"X-Forwarded-For": "1.2.3.4"},  # Mock constant IP
        )
        # We expect 401s (auth failed) not 429s yet
        assert response.status_code in (401, 200)

    # 6th time should be 429
    response = client.post(
        "/api/auth/token",
        data={"username": "test", "password": "password"},
        headers={"X-Forwarded-For": "1.2.3.4"},
    )
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json().get("error", "")


def test_rate_limiting_chat(client, enable_rate_limiter, system_db_session):
    """Verify chat rate limiting."""
    from backend.main import get_current_user

    # Mock user
    mock_user = MagicMock(id="u1", org_id="o1", is_admin=True)

    # Override dependency
    app.dependency_overrides[get_current_user] = lambda: mock_user

    # Mock storage conversation lookup to return valid conversation owned by u1
    with patch("backend.storage.get_conversation") as mock_get_conv:
        mock_get_conv.return_value = {"id": "c1", "user_id": "u1", "messages": []}

        # Mock other dependencies that run in send_message
        with (
            patch("backend.main._handle_conversation_title", new_callable=AsyncMock),
            patch("backend.main.run_full_council", new_callable=AsyncMock) as mock_council,
            patch("backend.main._record_voting_history"),
            patch("backend.storage.add_user_message"),
            patch("backend.storage.add_assistant_message"),
            patch("backend.main.get_org_api_config") as mock_get_config,
        ):
            mock_council.return_value = (["s1"], ["s2"], "s3", {"label_to_model": {}})
            mock_get_config.return_value = ("api_key", "base_url")

            # Hit chat 5 times
            for _ in range(5):
                res = client.post(
                    "/api/conversations/c1/message",
                    json={"content": "hi"},
                    headers={"X-Forwarded-For": "10.0.0.1"},
                )
                assert res.status_code == 200

            # 6th time
            res = client.post(
                "/api/conversations/c1/message",
                json={"content": "hi"},
                headers={"X-Forwarded-For": "10.0.0.1"},
            )
            assert res.status_code == 429

    # Clean up override
    app.dependency_overrides.clear()
