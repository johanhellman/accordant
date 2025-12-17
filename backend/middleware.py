import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# Context variable to store request ID for logging access
request_id_context: ContextVar[str] = ContextVar("request_id", default="UNKNOWN")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware that:
    1. Generates a unique UUID for each request (or uses X-Request-ID if provided).
    2. Sets it in a ContextVar for structured logging.
    3. Adds it to the X-Request-ID response header.
    """

    async def dispatch(self, request: Request, call_next):
        # Prefer existing ID (for tracing across services), else generate new
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Set context var
        token = request_id_context.set(req_id)

        response = await call_next(request)

        # Add to response headers
        response.headers["X-Request-ID"] = req_id

        # Clean up context var (good practice, though not strictly required for asyncio task scope)
        request_id_context.reset(token)

        return response
