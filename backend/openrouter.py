"""OpenRouter API client for making LLM requests."""

import asyncio
import logging
from typing import Any

import httpx

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

    This function handles retries with exponential backoff for transient errors
    (429 Too Many Requests, 5xx server errors, timeouts). It uses a semaphore
    to limit concurrent requests according to MAX_CONCURRENT_REQUESTS.

    Args:
        model: OpenRouter model identifier (e.g., "openai/gpt-4o")
        messages: List of message dicts with 'role' and 'content' keys
        timeout: Request timeout in seconds (default: LLM_REQUEST_TIMEOUT)
        temperature: Optional temperature setting (0.0 to 1.0) for model output

    Returns:
        Dict with 'content' (str) and optional 'reasoning_details' keys if successful,
        None if the request failed after all retries.

    Raises:
        No exceptions are raised; all errors are caught and logged, returning None.

    Example:
        >>> messages = [{"role": "user", "content": "Hello"}]
        >>> response = await query_model("openai/gpt-4o", messages)
        >>> if response:
        ...     print(response['content'])
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
        for attempt in range(LLM_MAX_RETRIES):
            try:
                logger.debug(f"Querying model {model} (attempt {attempt + 1}/{LLM_MAX_RETRIES})...")
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(base_url, headers=headers, json=payload)
                    response.raise_for_status()

                    data = response.json()
                    message = data["choices"][0]["message"]
                    logger.debug(f"Model {model} responded successfully.")

                    return {
                        "content": message.get("content"),
                        "reasoning_details": message.get("reasoning_details"),
                    }

            except httpx.HTTPStatusError as e:
                # Retry on 429 (Too Many Requests) or 5xx (Server Errors)
                if (
                    e.response.status_code == 429 or e.response.status_code >= 500
                ) and attempt < LLM_MAX_RETRIES - 1:
                    wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s...
                    logger.warning(
                        f"Model {model} failed with {e.response.status_code}. Retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                    continue

                # If not retryable or max retries reached
                logger.error(f"Error querying model {model}: {e}")
                return None

            except httpx.TimeoutException:
                if attempt < LLM_MAX_RETRIES - 1:
                    wait_time = 2**attempt
                    logger.warning(f"Model {model} timed out. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue

                logger.error(f"Error querying model {model}: Request timed out after {timeout}s")
                return None

            except Exception as e:
                logger.error(f"Error querying model {model}: {e}")
                return None

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
