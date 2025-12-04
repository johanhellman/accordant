"""Service for interacting with LLM providers (OpenRouter/LiteLLM)."""

import logging
from datetime import datetime, timedelta
from typing import Any

import httpx

# from .config import OPENROUTER_API_KEY, OPENROUTER_API_URL # Removed global import

logger = logging.getLogger(__name__)

# Cache for models list
# Cache for models list, keyed by base_url
# Structure: { base_url: { "models": [...], "timestamp": datetime } }
_MODELS_CACHE: dict[str, dict[str, Any]] = {}
_CACHE_TTL = timedelta(minutes=60)  # Cache models for 1 hour


async def get_available_models(api_key: str, base_url: str) -> list[dict[str, Any]]:
    """
    Fetch available models from the configured LLM provider.

    Args:
        api_key: The API key to use.
        base_url: The base URL for the LLM provider.

    Returns:
        List of model dicts with 'id', 'name', 'provider' keys.
    """
    global _MODELS_CACHE

    # Check cache for this specific base_url
    if base_url in _MODELS_CACHE:
        cache_entry = _MODELS_CACHE[base_url]
        if (datetime.now() - cache_entry["timestamp"]) < _CACHE_TTL:
            return cache_entry["models"]

    try:
        # Determine provider URL (OpenRouter vs Generic/LiteLLM)
        # If OPENROUTER_API_URL is the default OpenRouter URL, use their models endpoint
        # Otherwise assume OpenAI-compatible /models endpoint

        if "openrouter.ai" in base_url:
            models_url = "https://openrouter.ai/api/v1/models"
        else:
            # Strip /chat/completions and append /models
            _base = base_url.replace("/chat/completions", "")
            models_url = f"{_base}/models"

        logger.info(f"Fetching models from {models_url}")

        headers = {
            "Authorization": f"Bearer {api_key}",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(models_url, headers=headers)
            response.raise_for_status()
            data = response.json()

            raw_models = data.get("data", [])
            processed_models = []

            for m in raw_models:
                model_id = m.get("id")
                if not model_id:
                    continue

                # Extract provider from ID (e.g., "openai/gpt-4" -> "openai")
                parts = model_id.split("/")
                provider = parts[0] if len(parts) > 1 else "unknown"
                name = m.get("name", model_id)

                processed_models.append({"id": model_id, "name": name, "provider": provider})

            # Update cache for this base_url
            _MODELS_CACHE[base_url] = {"models": processed_models, "timestamp": datetime.now()}

            return processed_models

    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        # Return empty list or fallback?
        return []
