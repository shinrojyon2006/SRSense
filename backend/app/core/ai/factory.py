"""
AI Provider Factory.

Instantiates configured AI Provider implementation.
"""

from app.core.ai.heuristics_provider import HeuristicsAIProvider
from app.core.ai.provider_interface import BaseAIProvider


def get_ai_provider() -> BaseAIProvider:
    """Return the configured AI Provider instance (defaults to HeuristicsAIProvider)."""
    return HeuristicsAIProvider()
