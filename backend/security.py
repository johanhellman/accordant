"""Security and encryption utilities."""

import logging
import os

from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Load or generate encryption key
_ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
_ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

if not _ENCRYPTION_KEY:
    if _ENVIRONMENT == "production":
        logger.critical("ENCRYPTION_KEY not found in production environment.")
        raise ValueError("ENCRYPTION_KEY must be set in production.")
    else:
        logger.warning(
            "ENCRYPTION_KEY not found in environment variables. Generating a temporary key for this session."
        )
        _ENCRYPTION_KEY = Fernet.generate_key().decode()

try:
    _fernet = Fernet(
        _ENCRYPTION_KEY.encode() if isinstance(_ENCRYPTION_KEY, str) else _ENCRYPTION_KEY
    )
except Exception as e:
    logger.error(f"Invalid ENCRYPTION_KEY: {e}")
    raise ValueError("Invalid ENCRYPTION_KEY provided.") from e


def encrypt_value(value: str) -> str:
    """Encrypt a string value."""
    if not value:
        return ""
    return _fernet.encrypt(value.encode()).decode()


def decrypt_value(token: str) -> str:
    """Decrypt a string value."""
    if not token:
        return ""
    try:
        return _fernet.decrypt(token.encode()).decode()
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise ValueError("Decryption failed") from e
