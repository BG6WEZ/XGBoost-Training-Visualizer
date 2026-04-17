"""
Structured logging configuration for production and development.

Supports:
- LOG_FORMAT=text (default): Human-readable format for local development
- LOG_FORMAT=json: Machine-parseable JSON for production log aggregation
"""

import logging
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any


class JsonFormatter(logging.Formatter):
    """
    JSON log formatter for production environments.
    Outputs valid JSON with structured fields.
    """

    def __init__(self):
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "logger": record.name,
        }

        # Add task_id if available
        if hasattr(record, "task_id"):
            log_entry["task_id"] = record.task_id

        # Add exception info
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False, default=str)


class TextFormatter(logging.Formatter):
    """
    Human-readable log formatter for local development.
    """

    def __init__(self):
        super().__init__(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


def get_log_format() -> str:
    """Get the configured log format from environment."""
    return os.getenv("LOG_FORMAT", "text").lower()


def setup_logging() -> None:
    """
    Configure application-wide logging.

    Call this once during application startup.
    """
    log_format = get_log_format()

    # Create root logger config
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)

    # Set formatter based on config
    if log_format == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(TextFormatter())

    root_logger.addHandler(handler)

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(
        "Worker logging configured: format=%s, level=%s",
        log_format,
        logging.getLevelName(root_logger.level),
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    """
    return logging.getLogger(name)