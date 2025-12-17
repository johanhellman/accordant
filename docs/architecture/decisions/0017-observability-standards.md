# 17. Observability Standards

Date: 2025-12-17

## Status

Accepted

## Context

As the application scales, debugging issues across distributed components (backend, potential workers, database) becomes difficult with unstructured logs and inconsistent error responses. We lack a unified way to trace a request from entry to exit.

## Decision

We will adopt the following observability standards:

1.  **Standardized Error Responses**: All API errors will return a consistent JSON structure.
    ```json
    {
      "error": {
        "code": "RESOURCE_NOT_FOUND",
        "message": "Conversation not found",
        "request_id": "req_123..."
      }
    }
    ```

2.  **Structured JSON Logging**: All application logs will be output in JSON format in production environments. This enables easy parsing by log aggregators.
    Fields include: `timestamp`, `level`, `message`, `module`, `function`, `line`, and `correlation_id`.

3.  **Request Tracing**: A unique `X-Request-ID` header will be assigned to every incoming request. This ID will be propagated to all logs generated during the request's lifecycle via `contextvars`.

## Consequences

### Positive
-   Easier debugging and log searching.
-   Frontend clients can reliably parse error codes instead of regex-matching error strings.
-   Correlation of logs across different modules.

### Negative
-   Logs are less human-readable in the raw console (though tools like `jq` help).
-   Requires updates to existing tests that assert error formats (completed).
