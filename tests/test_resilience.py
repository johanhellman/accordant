
import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import httpx
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.openrouter import query_model, get_semaphore
from backend.main import app
from backend.limiter import limiter

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

    # Mock response to fail twice with 500, then succeed
    mock_responses = [
        httpx.Response(500),
        httpx.Response(503),
        httpx.Response(200, json={
            "choices": [{"message": {"content": "Success", "reasoning_details": None}}]
        })
    ]

    with patch("httpx.AsyncClient.post", side_effect=mock_responses) as mock_post:
        # Patch sleep to speed up test
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await query_model(model, messages, api_key, base_url)

            assert result["content"] == "Success"
            assert mock_post.call_count == 3  # Initial + 2 failures
            assert mock_sleep.call_count == 2 # 2 sleeps

@pytest.mark.asyncio
async def test_openrouter_429_retry():
    """Test retry on 429 Too Many Requests."""
    model = "openai/gpt-4o"
    messages = [{"role": "user", "content": "hello"}]
    
    mock_responses = [
        httpx.Response(429),
        httpx.Response(200, json={
            "choices": [{"message": {"content": "After 429", "reasoning_details": None}}]
        })
    ]
    
    with patch("httpx.AsyncClient.post", side_effect=mock_responses) as mock_post:
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await query_model(model, messages, "k", "u")
            assert result["content"] == "After 429"
            assert mock_post.call_count == 2

def test_rate_limiting_login(client, enable_rate_limiter):
    """Verify login rate limit (5/minute) triggers 429."""
    
    # Hit login 5 times (allowed)
    for _ in range(5):
        response = client.post(
            "/api/auth/token", 
            data={"username": "test", "password": "password"},
            headers={"X-Forwarded-For": "1.2.3.4"} # Mock constant IP
        )
        # We expect 401s (auth failed) not 429s yet
        assert response.status_code in (401, 200)

    # 6th time should be 429
    response = client.post(
        "/api/auth/token", 
        data={"username": "test", "password": "password"},
        headers={"X-Forwarded-For": "1.2.3.4"}
    )
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json().get("error", "")

def test_rate_limiting_chat(client, enable_rate_limiter, system_db_session):
    """Verify chat rate limiting."""
    # Note: We need a valid user for this one to bypass auth check before rate limit check?
    # SlowAPI middleware runs before deps? Yes, usually. But endpoint decorator runs at endpoint level.
    # FastAPI depends runs before view function body.
    # So if auth fails, we might get 401 before 429 if the limiter is on the function.
    # But usually limiter is checked early.
    
    # However, since we decorate the *function*, FastAPI dependencies (user auth) run first.
    # So we need to be authenticated or at least bypass auth to hit the limit.
    # Actually, slowapi checks limits *before* executing the function body, 
    # but after middleware. If it's a decorator, it wraps the function.
    # Dependencies are part of the function call signature handling in FastAPI.
    
    # If standard Depends(get_current_user) fails, it raises 401.
    # So we need to authorize first.
    
    # Let's verify this behavior:
    # If we are unauthenticated, we expect 401, regardless of rate limit (unless middleware checks it).
    # Since we used @limiter.limit decorator, it runs *when the route is matched/called*.
    
    # Let's assume we need auth.
    from backend.auth import create_access_token
    token = create_access_token({"sub": "admin"})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Forwarded-For": "5.6.7.8"
    }

    # Ensure user exists for auth dependency (mock it)
    # Or just mock get_current_user dependency 
    with patch("backend.main.get_current_user") as mock_user:
        mock_user.return_value = MagicMock(id="u1", org_id="o1", is_admin=True)

        # Hit chat 5 times
        for _ in range(5):
            # We don't care if conversation lookup fails (404), as long as it's not 429
            client.post("/api/conversations/c1/message", json={"content": "hi"}, headers=headers)
        
        # 6th time
        res = client.post("/api/conversations/c1/message", json={"content": "hi"}, headers=headers)
        assert res.status_code == 429
