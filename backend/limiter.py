"""Rate limiting configuration."""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize Limiter
# Uses in-memory storage by default, which is sufficient for single-instance deployment.
# Keying by remote address (IP).
limiter = Limiter(key_func=get_remote_address)
