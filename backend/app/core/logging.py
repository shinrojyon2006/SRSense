"""
Core Logging — Re-exports the structured logger from shared utilities.

All application code should use this module for logging.
The underlying implementation includes Request ID correlation support.
"""

from app.utils.logger import get_logger

logger = get_logger("srsense")

__all__ = ["logger", "get_logger"]
