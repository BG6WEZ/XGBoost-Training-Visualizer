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
import contextvars
from datetime import datetime, timezone
from typing import Any

# Context variable for request_id (thread-safe async context)
request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)


class RequestIdFilter(logging.Filter):
    """
    Logging filter that injects request_id from context variable.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True


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
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request_id if available (injected by middleware)
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id

        # Add exception info
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add any extra fields
        extra_fields = {
            key: value
            for key, value in record.__dict__.items()
            if key not in (
                "name", "msg", "args", "created", "relativeCreated",
                "exc_info", "exc_text", "stack_info", "lineno",
                "funcName", "module", "levelname", "levelno",
                "pathname", "filename", "msecs", "thread", "threadName",
                "process", "processName", "message", "taskName",
                "request_id",
            )
        }
        if extra_fields:
            log_entry.update(extra_fields)

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

    def format(self, record: logging.LogRecord) -> str:
        # Add request_id if available and non-null
        if hasattr(record, "request_id") and record.request_id is not None:
            original_msg = record.getMessage()
            record.msg = f"[{record.request_id}] {original_msg}"
            record.args = ()
        return super().format(record)


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

    # Add request_id filter to the HANDLER so it applies to ALL records
    # that reach it, regardless of which logger emitted them.
    # (Root logger filters only apply to the root logger itself, not
    #  to child loggers whose propagate=True sends records up the hierarchy.)
    request_id_filter = RequestIdFilter()
    handler.addFilter(request_id_filter)

    # Set formatter based on config
    if log_format == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(TextFormatter())

    root_logger.addHandler(handler)

    # Also add the filter to the root logger so non-propagating loggers
    # that directly log to root still get request_id
    root_logger.addFilter(request_id_filter)

    # Set log levels for noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured: format=%s, level=%s",
        log_format,
        logging.getLevelName(root_logger.level),
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    """
    return logging.getLogger(name)