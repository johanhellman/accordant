# ADR-004: Router-Independent LLM API Integration

**Status**: Accepted  
**Date**: 2025-11-25  
**Deciders**: Project Team

## Context

The application needs to query multiple LLM providers. Options included:
- Direct API integration with each provider (OpenAI, Anthropic, Google, etc.)
- A unified API gateway like OpenRouter or LiteLLM
- Self-hosted models

We needed a solution that:
- Supports multiple providers with a single API
- Handles authentication and rate limiting
- Provides access to cutting-edge models
- Minimizes integration complexity
- Allows flexibility to switch between different router services

## Decision

We will use a router-independent abstraction that supports multiple unified API gateways:
- **OpenRouter** (original implementation, default)
- **LiteLLM** (added support for router independence)

The system abstracts the router implementation, allowing users to configure either OpenRouter or LiteLLM via environment variables.

## Consequences

### Positive
- **Single Integration**: One API client instead of multiple provider clients
- **Model Variety**: Access to models from OpenAI, Anthropic, Google, xAI, etc.
- **Simplified Auth**: Single API key instead of managing multiple keys
- **Router Flexibility**: Can switch between OpenRouter and LiteLLM via configuration
- **Abstraction Layer**: Router implementation is abstracted, making it easy to add more routers
- **Rate Limiting**: Router services handle provider-specific rate limits
- **Cost Management**: Unified billing through chosen router service

### Negative
- **Dependency**: Relies on router service availability
- **Additional Cost**: Router services may add a markup on top of provider costs
- **Less Control**: Can't use provider-specific features directly
- **API Changes**: Subject to router service API evolution
- **Configuration Complexity**: Users must understand which router they're using

### Neutral
- API key stored in `.env` file (gitignored)
- Supports both streaming and non-streaming modes
- Retry logic with exponential backoff for transient errors
- Router abstraction allows for future expansion to other services
- See `backend/openrouter.py` for implementation (note: filename reflects original implementation, but code is router-independent)

## Implementation Notes

- **Router Configuration**:
  - API key: `LLM_API_KEY` (preferred) or `OPENROUTER_API_KEY` (fallback)
  - API URL: `LLM_API_URL` (preferred) or defaults to OpenRouter endpoint
  - This allows switching between OpenRouter and LiteLLM by changing environment variables
- **Default Behavior**: If no `LLM_API_URL` is set, defaults to OpenRouter (`https://openrouter.ai/api/v1/chat/completions`)
- **LiteLLM Support**: Set `LLM_API_URL` to your LiteLLM endpoint (e.g., `http://localhost:4000/v1/chat/completions`)
- Semaphore-based concurrency control (configurable via `MAX_CONCURRENT_REQUESTS`)
- Request timeout configurable via `LLM_REQUEST_TIMEOUT`
- Retry logic handles 429 (rate limit) and 5xx (server error) responses
- See `backend/config.py` for configuration options
- Note: The module is still named `openrouter.py` for historical reasons, but the implementation is router-independent

