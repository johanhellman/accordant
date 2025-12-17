# ADR-022: Resilience Patterns (Retries & Rate Limiting)

## Status
Accepted

## Date
2025-12-17

## Context
As the Accordant platform scales, it faces two primary reliability risks:
1.  **External Service Instability**: Reliance on external LLM APIs (OpenRouter, direct providers) means network flakes, rate limits (429), or temporary outages (5xx) can disrupt user workflows.
2.  **Internal Abuse/Overload**: Protecting the API from abuse or accidental overload (e.g., rapid-fire requests) is critical for system stability.

Previously, retries were handled via ad-hoc loops, and there was no rate limiting mechanism.

## Decision
We have decided to implement standardized resilience patterns using established libraries:

1.  **Robust Retries via `tenacity`**:
    *   We will use the `tenacity` library to handle retries for external API calls.
    *   **Strategy**: Exponential backoff (jittered) to prevent thundering herds.
    *   **Scope**: `backend/openrouter.py`, `backend/llm_service.py`.
    *   **Configuration**: Defaults to 3 retries, catching `httpx.ConnectTimeout`, `httpx.ReadTimeout`, and `httpx.HTTPStatusError` (for 5xx and 429).

2.  **API Rate Limiting via `slowapi`**:
    *   We will use `slowapi` (based on `limits`) to implement API rate limiting.
    *   **Storage**: In-memory storage for the single-instance backend (extensible to Redis if needed).
    *   **Strategy**: Keyed by IP address (`get_remote_address`).
    *   **Limits**:
        *   Auth endpoints (`/api/auth/token`, `/api/auth/register`): **5/minute**.
        *   Chat endpoints (`/api/conversations/*/message`): **5/minute**.
    *   **Handling**: Returns `429 Too Many Requests` with a clear error message.

## Consequences
### Positive
*   **Improved Reliability**: Transient external errors are handled transparently, reducing user-facing failures.
*   **Protection**: The backend is protected against brute-force login attempts and chat API abuse.
*   **Maintainability**: Standard libraries replace custom, error-prone retry logic.
*   **Testability**: Configuration is centralized and mocks can verify behavior easily.

### Negative
*   **Complexity**: Introduced new dependencies (`tenacity`, `slowapi`).
*   **User Experience**: Rate limits might affect legitimate power users if set too aggressively (can be tuned via configuration).
*   **Statefulness**: In-memory rate limiting resets on restart (acceptable for now).

## References
*   [Tenacity Documentation](https://tenacity.readthedocs.io/)
*   [SlowAPI Documentation](https://slowapi.readthedocs.io/)
