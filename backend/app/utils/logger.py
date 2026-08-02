"""
Centralized structured logging with Request ID (Correlation ID) support.
"""

import contextvars
import logging
import sys
from typing import Optional

from app.core.config import get_settings

settings = get_settings()

# ContextVar to track request IDs across async tasks
request_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)


class RequestIDFilter(logging.Filter):
    """Logging filter that injects the current request ID into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get() or "system"
        return True


def get_logger(name: str = "srsense") -> logging.Logger:
    """
    Create and return a configured logger instance with Request ID tracking.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        logger.setLevel(log_level)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | [%(request_id)s] | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        handler.addFilter(RequestIDFilter())
        logger.addHandler(handler)

    return logger
