import logging
import os
import sys
from datetime import datetime

from pythonjsonlogger import jsonlogger

# Import context var for correlation ID
from .middleware import request_id_context


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)

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

    # Silence noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    # logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logging.info("JSON Logging initialized", extra={"log_level": log_level_str})
