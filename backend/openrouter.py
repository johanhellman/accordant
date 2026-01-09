"""OpenRouter API client for making LLM requests."""

import asyncio
import logging
from typing import Any

import httpx
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .config import LLM_MAX_RETRIES, LLM_REQUEST_TIMEOUT, MAX_CONCURRENT_REQUESTS

logger = logging.getLogger(__name__)

# Global semaphore for concurrency control
_SEMAPHORE = None


def get_semaphore():
    """
    Get or create the global semaphore for concurrency control.

    Returns:
        asyncio.Semaphore: The global semaphore instance, initialized with MAX_CONCURRENT_REQUESTS.
    """
    global _SEMAPHORE
    if _SEMAPHORE is None:
        _SEMAPHORE = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    return _SEMAPHORE


@retry(
    stop=stop_after_attempt(LLM_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception_type((httpx.ConnectTimeout, httpx.ReadTimeout, httpx.HTTPStatusError)),
    before_sleep=before_sleep_log(logger, logging.DEBUG),
    reraise=True,
)
async def _execute_request(
    client: httpx.AsyncClient, base_url: str, headers: dict, payload: dict
) -> httpx.Response:
    """Execute request with retry logic."""
    response = await client.post(base_url, headers=headers, json=payload)
    # Raise error for status codes we want to retry (e.g. 5xx, 429)
    # Note: raise_for_status raises HTTPStatusError
    if response.status_code == 429 or response.status_code >= 500:
        response.raise_for_status()
    # For other errors (e.g. 400, 401), we return response and handle it in caller
    return response


async def query_model(
    model: str,
    messages: list[dict[str, str]],
    api_key: str,
    base_url: str,
    timeout: float = LLM_REQUEST_TIMEOUT,
    temperature: float | None = None,
) -> dict[str, Any] | None:
    """
    Query a single model via OpenRouter API.

    This function handles retries with exponential backoff via tenacity.
    It uses a semaphore to limit concurrent requests.

    Args:
        model: OpenRouter model identifier (e.g., "openai/gpt-4o")
        messages: List of message dicts with 'role' and 'content' keys
        timeout: Request timeout in seconds (default: LLM_REQUEST_TIMEOUT)
        temperature: Optional temperature setting (0.0 to 1.0) for model output

    Returns:
        Dict with 'content' and optional 'reasoning_details' keys if successful,
        None if the request failed after all retries.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
    }

    if temperature is not None:
        payload["temperature"] = temperature

    semaphore = get_semaphore()

    async with semaphore:
        try:
            logger.debug(f"Querying model {model}...")
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await _execute_request(client, base_url, headers, payload)
                response.raise_for_status()  # Check for other errors (400, 401, etc.)

                data = response.json()
                message = data["choices"][0]["message"]
                logger.debug(f"Model {model} responded successfully.")

                return {
                    "content": message.get("content"),
                    "reasoning_details": message.get("reasoning_details"),
                }
        except Exception as e:
            logger.error(f"Error querying model {model}: {e}")
            return None


async def query_models_parallel(
    models: list[str], messages: list[dict[str, str]], api_key: str, base_url: str
) -> dict[str, dict[str, Any] | None]:
    """
    Query multiple models in parallel using asyncio.gather.

    All models are queried concurrently, with concurrency controlled by
    the global semaphore. Each model query is independent and failures
    in one model don't affect others.

    Args:
        models: List of OpenRouter model identifiers to query
        messages: List of message dicts with 'role' and 'content' keys
                 to send to each model

    Returns:
        Dict mapping each model identifier to its response dict.
        Response dicts have 'content' and optional 'reasoning_details' keys.
        Failed queries map to None.

    Example:
        >>> models = ["openai/gpt-4o", "anthropic/claude-3-opus"]
        >>> messages = [{"role": "user", "content": "Hello"}]
        >>> responses = await query_models_parallel(models, messages)
        >>> for model, response in responses.items():
        ...     if response:
        ...         print(f"{model}: {response['content']}")
    """
    logger.info(f"Querying {len(models)} models in parallel.")

    # Create tasks for all models
    tasks = [query_model(model, messages, api_key, base_url) for model in models]

    # Wait for all to complete
    responses = await asyncio.gather(*tasks)

    # Map models to their responses
    return dict(zip(models, responses, strict=True))
