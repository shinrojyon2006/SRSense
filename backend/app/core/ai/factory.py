"""
AI Provider Factory — Phase B Real AI Integration.

Provider selection is driven EXCLUSIVELY by the AI_PROVIDER environment variable.
API keys are backend-only env vars — never logged, never exposed to frontend.

Selection logic:
  AI_PROVIDER=heuristic  → HeuristicsAIProvider (default, CI-safe, no external calls)
  AI_PROVIDER=gemini     → GeminiAIProvider     (requires GEMINI_API_KEY)
  AI_PROVIDER=openai     → OpenAIAIProvider     (requires OPENAI_API_KEY)

On missing key or unknown provider → falls back to HeuristicsAIProvider with a warning.
"""

import logging

from app.core.ai.provider_interface import BaseAIProvider
from app.core.ai.heuristics_provider import HeuristicsAIProvider
from app.core.config import get_settings

logger = logging.getLogger(__name__)


def get_ai_provider() -> BaseAIProvider:
    """Return the configured AI provider based on environment settings.

    SECURITY: API keys are read from settings (env vars) only.
    They are never logged, never returned to callers, never serialized.
    """
    settings = get_settings()
    provider_name = (settings.AI_PROVIDER or "heuristic").lower().strip()

    if provider_name == "gemini":
        if not settings.GEMINI_API_KEY:
            logger.warning(
                "AI_PROVIDER=gemini but GEMINI_API_KEY is empty. "
                "Falling back to HeuristicsAIProvider."
            )
            return HeuristicsAIProvider()
        try:
            from app.core.ai.gemini_provider import GeminiAIProvider
            logger.info("AI provider: Gemini (gemini-1.5-flash)")
            return GeminiAIProvider(
                api_key=settings.GEMINI_API_KEY,
                timeout=settings.AI_REQUEST_TIMEOUT_SECONDS,
                max_retries=settings.AI_MAX_RETRIES,
            )
        except ImportError as e:
            logger.error("GeminiAIProvider import failed: %s. Falling back to heuristics.", e)
            return HeuristicsAIProvider()

    elif provider_name == "openai":
        if not settings.OPENAI_API_KEY:
            logger.warning(
                "AI_PROVIDER=openai but OPENAI_API_KEY is empty. "
                "Falling back to HeuristicsAIProvider."
            )
            return HeuristicsAIProvider()
        try:
            from app.core.ai.openai_provider import OpenAIAIProvider
            logger.info("AI provider: OpenAI (gpt-4o-mini)")
            return OpenAIAIProvider(
                api_key=settings.OPENAI_API_KEY,
                timeout=settings.AI_REQUEST_TIMEOUT_SECONDS,
                max_retries=settings.AI_MAX_RETRIES,
            )
        except ImportError as e:
            logger.error("OpenAIAIProvider import failed: %s. Falling back to heuristics.", e)
            return HeuristicsAIProvider()

    elif provider_name == "heuristic":
        logger.info("AI provider: HeuristicsAIProvider (deterministic)")
        return HeuristicsAIProvider()

    else:
        logger.warning(
            "Unknown AI_PROVIDER value '%s'. Valid options: heuristic, gemini, openai. "
            "Falling back to HeuristicsAIProvider.",
            provider_name,
        )
        return HeuristicsAIProvider()
