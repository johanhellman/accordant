"""Path configuration and validation."""

import logging
import os

logger = logging.getLogger(__name__)


def validate_file_path(path: str, base_dir: str = None, allow_absolute: bool = True) -> str:
    """
    Validate and normalize a file path to prevent directory traversal attacks.

    Args:
        path: The file path to validate
        base_dir: Base directory to resolve relative paths against (default: current working directory)
        allow_absolute: Whether to allow absolute paths (default: True)

    Returns:
        Normalized absolute path

    Raises:
        ValueError: If path contains directory traversal attempts or is invalid
    """
    if not path:
        raise ValueError("Path cannot be empty")

    # Check for directory traversal attempts in the original path
    if ".." in path or path.startswith("/") and not allow_absolute:
        # For relative paths, check if normalization would escape base_dir
        if not os.path.isabs(path) and ".." in path:
            # This will be caught when we check if it's within base_dir
            pass
        elif os.path.isabs(path) and not allow_absolute:
            raise ValueError(f"Absolute paths not allowed: {path}")

    # Resolve to absolute path
    if os.path.isabs(path):
        if not allow_absolute:
            raise ValueError(f"Absolute paths not allowed: {path}")
        resolved = os.path.abspath(path)
    else:
        base = os.path.abspath(base_dir) if base_dir else os.getcwd()
        resolved = os.path.abspath(os.path.join(base, path))

    # Normalize the path
    normalized = os.path.normpath(resolved)

    # Ensure the resolved path is within the base directory (if specified)
    # This prevents directory traversal even if '..' was in the original path
    if base_dir:
        base_abs = os.path.abspath(base_dir)
        # Use os.path.commonpath to ensure normalized is within base_abs
        try:
            common = os.path.commonpath([base_abs, normalized])
            if common != base_abs:
                raise ValueError(f"Path outside allowed directory: {path}")
        except ValueError:
            # commonpath raises ValueError if paths are on different drives (Windows)
            # In that case, check if normalized starts with base_abs
            if not os.path.normpath(normalized).startswith(os.path.normpath(base_abs)):
                raise ValueError(f"Path outside allowed directory: {path}") from None

    return normalized


def validate_directory_path(path: str, base_dir: str = None, allow_absolute: bool = True) -> str:
    """
    Validate and normalize a directory path to prevent directory traversal attacks.

    Args:
        path: The directory path to validate
        base_dir: Base directory to resolve relative paths against (default: current working directory)
        allow_absolute: Whether to allow absolute paths (default: True)

    Returns:
        Normalized absolute path

    Raises:
        ValueError: If path contains directory traversal attempts or is invalid
    """
    validated = validate_file_path(path, base_dir, allow_absolute)
    return validated


# Get project root directory (parent of backend directory)
# Assuming this file is in backend/config/paths.py, so parent is backend, grandparent is root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Logging Configuration
LOG_DIR_ENV = os.getenv("LOG_DIR", "logs")
try:
    LOG_DIR = validate_directory_path(LOG_DIR_ENV, base_dir=PROJECT_ROOT, allow_absolute=True)
except ValueError as e:
    logger.warning(f"Invalid LOG_DIR '{LOG_DIR_ENV}': {e}. Using default 'logs' directory.")
    LOG_DIR = os.path.join(PROJECT_ROOT, "logs")

LOG_FILE_ENV = os.getenv("LOG_FILE", os.path.join(LOG_DIR, "llm_council.log"))
try:
    LOG_FILE = validate_file_path(LOG_FILE_ENV, base_dir=PROJECT_ROOT, allow_absolute=True)
except ValueError as e:
    logger.warning(f"Invalid LOG_FILE '{LOG_FILE_ENV}': {e}. Using default log file.")
    LOG_FILE = os.path.join(LOG_DIR, "llm_council.log")

LOG_RETENTION_DAYS = int(os.getenv("LOG_RETENTION_DAYS", "30"))
