import logging
import os
import sys
from datetime import datetime

from pythonjsonlogger import jsonlogger

# Import context var for correlation ID
from .middleware import request_id_context


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        # Standard fields
        if not log_record.get("timestamp"):
            now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            log_record["timestamp"] = now

        if log_record.get("level"):
            log_record["level"] = log_record["level"].upper()
        else:
            log_record["level"] = record.levelname

        log_record["module"] = record.module

        # Add Correlation ID from context
        try:
            req_id = request_id_context.get()
            if req_id != "UNKNOWN":
                log_record["correlation_id"] = req_id
        except LookupError:
            pass  # Context var not set


def setup_logging():
    """
    Configure the root logger for the application with JSON formatting.
    """
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    # valid_json_fields = ["timestamp", "level", "name", "message", "module", "correlation_id"]
    formatter = CustomJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s %(module)s")

    # Create a handler for stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    if root_logger.handlers:
        root_logger.handlers.clear()

    root_logger.addHandler(handler)

    # Configure File Handler
    try:
        from logging.handlers import RotatingFileHandler

        from .config.paths import LOG_FILE, LOG_RETENTION_DAYS

        # Create logs directory if it doesn't exist (handled in paths.py validation usually, but safe to check)
        log_dir = os.path.dirname(LOG_FILE)
        os.makedirs(log_dir, exist_ok=True)

        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=LOG_RETENTION_DAYS,
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        # Fallback to console only if file logging fails (e.g. permissions)
        logging.error(f"Failed to setup file logging: {e}")

    # Silence noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    # logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logging.info(
        "JSON Logging initialized", extra={"log_level": log_level_str, "log_file": LOG_FILE}
    )
