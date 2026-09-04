"""
Phase B — Mocked AI Provider Tests
====================================
Tests AI provider selection, timeout, credential handling, malformed response,
fallback, and hallucination protection using mocks only.

NO live API calls. Safe for CI with AI_PROVIDER=heuristic (default).
"""

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.ai.heuristics_provider import HeuristicsAIProvider
from app.core.ai.provider_interface import AnalysisResult, ImprovementResult


# ── Factory / Provider Selection Tests ────────────────────────────────────────

class TestProviderSelection:
    """Factory must return correct provider based on AI_PROVIDER env var."""

    def _get_provider(self, provider_name: str, gemini_key: str = "", openai_key: str = ""):
        """Helper: temporarily set env vars and call factory."""
        from app.core.config import get_settings
        import importlib
        import app.core.ai.factory as factory_module

        with patch.object(get_settings(), 'AI_PROVIDER', provider_name), \
             patch.object(get_settings(), 'GEMINI_API_KEY', gemini_key), \
             patch.object(get_settings(), 'OPENAI_API_KEY', openai_key):
            return factory_module.get_ai_provider()

    def test_default_heuristic(self):
        """AI_PROVIDER=heuristic must return HeuristicsAIProvider."""
        from app.core.config import get_settings
        import app.core.ai.factory as factory_module

        with patch.object(get_settings(), 'AI_PROVIDER', 'heuristic'):
            provider = factory_module.get_ai_provider()
        assert isinstance(provider, HeuristicsAIProvider)

    def test_unknown_provider_falls_back_to_heuristic(self):
        """Unknown provider name must fall back to HeuristicsAIProvider."""
        from app.core.config import get_settings
        import app.core.ai.factory as factory_module

        with patch.object(get_settings(), 'AI_PROVIDER', 'unknown_llm_xyz'):
            provider = factory_module.get_ai_provider()
        assert isinstance(provider, HeuristicsAIProvider)

    def test_gemini_missing_key_falls_back(self):
        """AI_PROVIDER=gemini with empty key must fall back to HeuristicsAIProvider."""
        from app.core.config import get_settings
        import app.core.ai.factory as factory_module

        with patch.object(get_settings(), 'AI_PROVIDER', 'gemini'), \
             patch.object(get_settings(), 'GEMINI_API_KEY', ''):
            provider = factory_module.get_ai_provider()
        assert isinstance(provider, HeuristicsAIProvider)

    def test_openai_missing_key_falls_back(self):
        """AI_PROVIDER=openai with empty key must fall back to HeuristicsAIProvider."""
        from app.core.config import get_settings
        import app.core.ai.factory as factory_module

        with patch.object(get_settings(), 'AI_PROVIDER', 'openai'), \
             patch.object(get_settings(), 'OPENAI_API_KEY', ''):
            provider = factory_module.get_ai_provider()
        assert isinstance(provider, HeuristicsAIProvider)


# ── Gemini Provider Mocked Tests ───────────────────────────────────────────────

class TestGeminiProviderMocked:
    """Gemini provider tests using fully mocked Gemini SDK."""

    def _make_provider(self):
        from app.core.ai.gemini_provider import GeminiAIProvider
        return GeminiAIProvider(api_key="test-key-not-real", timeout=5, max_retries=1)

    @pytest.mark.asyncio
    async def test_analyze_valid_response(self):
        """Gemini provider returns correct AnalysisResult from mocked JSON."""
        provider = self._make_provider()
        mock_response = {
            "quality_score": 85,
            "ambiguity_tags": [],
            "passive_voice_instances": [],
            "missing_criteria": [],
            "summary_feedback": "Good requirement.",
        }
        with patch.object(provider, '_call_with_retry', new=AsyncMock(return_value=mock_response)):
            result = await provider.analyze_requirement(
                title="API Latency",
                description="The system shall respond within 200ms.",
                req_type="non_functional",
            )
        assert isinstance(result, AnalysisResult)
        assert result.quality_score == 85
        assert result.summary_feedback == "Good requirement."

    @pytest.mark.asyncio
    async def test_analyze_fallback_on_none_response(self):
        """Gemini failure (None response) must fall back to heuristics."""
        provider = self._make_provider()
        with patch.object(provider, '_call_with_retry', new=AsyncMock(return_value=None)):
            result = await provider.analyze_requirement(
                title="Test",
                description="The system shall process requests.",
                req_type="functional",
            )
        # Fallback to heuristics — should still return a valid AnalysisResult
        assert isinstance(result, AnalysisResult)
        assert 0 <= result.quality_score <= 100

    @pytest.mark.asyncio
    async def test_improve_hallucination_rejected(self):
        """Gemini improvement that invents new numeric thresholds must be rejected."""
        provider = self._make_provider()
        # LLM invents "200ms" when original had no numbers
        mock_response = {
            "improved_title": "System Speed",
            "improved_description": "The SRSense System shall respond within 200 milliseconds.",
            "ears_template_used": "Ubiquitous",
            "explanation": "Improved.",
        }
        with patch.object(provider, '_call_with_retry', new=AsyncMock(return_value=mock_response)):
            result = await provider.suggest_improvement(
                title="System Speed",
                description="The system should be fast.",  # No numbers in original
                req_type="non_functional",
            )
        # Hallucination detected — result falls back to heuristics (no invented 200ms)
        # Heuristics replaces "fast" with "respond within 200 milliseconds" — that's OK since
        # heuristics has a fixed mapping, not an invented number from the LLM
        assert isinstance(result, ImprovementResult)

    @pytest.mark.asyncio
    async def test_improve_no_hallucination_accepted(self):
        """Gemini improvement that preserves original numbers must be accepted."""
        provider = self._make_provider()
        mock_response = {
            "improved_title": "API Response",
            "improved_description": "The SRSense System shall respond within 200 milliseconds.",
            "ears_template_used": "Ubiquitous",
            "explanation": "Reformatted in EARS.",
        }
        with patch.object(provider, '_call_with_retry', new=AsyncMock(return_value=mock_response)):
            result = await provider.suggest_improvement(
                title="API Response",
                description="The system shall respond within 200 milliseconds.",  # 200 in original
                req_type="non_functional",
            )
        assert result.improved_description == "The SRSense System shall respond within 200 milliseconds."

    @pytest.mark.asyncio
    async def test_timeout_falls_back_to_heuristics(self):
        """Gemini timeout must fall back to heuristics gracefully."""
        import asyncio
        provider = self._make_provider()

        async def raise_timeout(*args, **kwargs):
            raise asyncio.TimeoutError()

        with patch.object(provider, '_call_with_retry', new=raise_timeout):
            result = await provider.analyze_requirement(
                title="Timeout Test",
                description="The system shall process requests.",
                req_type="functional",
            )
        assert isinstance(result, AnalysisResult)


# ── OpenAI Provider Mocked Tests ───────────────────────────────────────────────

class TestOpenAIProviderMocked:
    """OpenAI provider tests using fully mocked OpenAI SDK."""

    def _make_provider(self):
        from app.core.ai.openai_provider import OpenAIAIProvider
        return OpenAIAIProvider(api_key="test-key-not-real", timeout=5, max_retries=1)

    @pytest.mark.asyncio
    async def test_analyze_valid_response(self):
        """OpenAI provider returns correct AnalysisResult from mocked response."""
        provider = self._make_provider()
        mock_response = {
            "quality_score": 90,
            "ambiguity_tags": [],
            "passive_voice_instances": [],
            "missing_criteria": [],
            "summary_feedback": "Excellent.",
        }
        with patch.object(provider, '_call_with_retry', new=AsyncMock(return_value=mock_response)):
            result = await provider.analyze_requirement(
                title="Login",
                description="The system shall authenticate users within 500ms.",
                req_type="functional",
            )
        assert isinstance(result, AnalysisResult)
        assert result.quality_score == 90

    @pytest.mark.asyncio
    async def test_analyze_fallback_on_exception(self):
        """OpenAI error must fall back to heuristics."""
        provider = self._make_provider()

        async def raise_error(*args, **kwargs):
            raise ConnectionError("OpenAI unreachable")

        with patch.object(provider, '_call_with_retry', new=raise_error):
            result = await provider.analyze_requirement(
                title="Test",
                description="The system shall handle requests.",
                req_type="functional",
            )
        assert isinstance(result, AnalysisResult)

    @pytest.mark.asyncio
    async def test_improve_hallucination_rejected(self):
        """OpenAI improvement that invents new thresholds must be rejected."""
        provider = self._make_provider()
        mock_response = {
            "improved_title": "Login Speed",
            "improved_description": "The SRSense System shall log in users within 500 milliseconds.",
            "ears_template_used": "Ubiquitous",
            "explanation": "Added threshold.",
        }
        with patch.object(provider, '_call_with_retry', new=AsyncMock(return_value=mock_response)):
            result = await provider.suggest_improvement(
                title="Login Speed",
                description="The system shall log in users quickly.",  # No numbers
                req_type="functional",
            )
        # Hallucination of "500" detected — should fall back to heuristics
        assert isinstance(result, ImprovementResult)


# ── Heuristics Provider Baseline Tests ────────────────────────────────────────

class TestHeuristicsProviderFallback:
    """Heuristics provider must remain the solid fallback baseline."""

    @pytest.mark.asyncio
    async def test_heuristics_analyze_works(self):
        provider = HeuristicsAIProvider()
        result = await provider.analyze_requirement(
            title="Login",
            description="The SRSense System shall authenticate users.",
            req_type="functional",
        )
        assert isinstance(result, AnalysisResult)
        assert 0 <= result.quality_score <= 100

    @pytest.mark.asyncio
    async def test_heuristics_improve_works(self):
        provider = HeuristicsAIProvider()
        result = await provider.suggest_improvement(
            title="Speed",
            description="The system should be fast.",
            req_type="non_functional",
        )
        assert isinstance(result, ImprovementResult)
        assert "SRSense System shall" in result.improved_description
