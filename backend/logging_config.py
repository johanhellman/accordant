import logging
import os
import sys


def setup_logging():
    """
    Configure the root logger for the application.
    """
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    # Create a formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Create a handler for stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates if setup is called multiple times
    if root_logger.handlers:
        root_logger.handlers.clear()

    root_logger.addHandler(handler)

    # logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # File logging
    try:
        from logging.handlers import TimedRotatingFileHandler

        from .config import LOG_FILE, LOG_RETENTION_DAYS

        # Ensure log directory exists
        log_dir = os.path.dirname(LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_handler = TimedRotatingFileHandler(
            LOG_FILE, when="D", interval=1, backupCount=LOG_RETENTION_DAYS, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    except Exception as e:
        # Fallback if file logging fails, but don't crash app
        print(f"Failed to setup file logging: {e}", file=sys.stderr)

    logging.info(f"Logging initialized with level: {log_level_str}")
    if "file_handler" in locals():
        logging.info(f"Logging to file: {LOG_FILE}")
