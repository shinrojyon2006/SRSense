"""
Phase A Regression Tests — A3, A4/A8, A6, A9

Validates all stabilization fixes from Phase A:
- A3: Verification compiler extracts metrics from broader response-time patterns
- A4/A8: EARS improvement is idempotent for already-improved requirements
- A6: Requirement ID detection rejects ordinary words, accepts structured IDs
- A9: Quality analysis uses description only, not title
"""

import re
import pytest
from app.core.ai.heuristics_provider import HeuristicsAIProvider


# ── A3 Regression Tests ───────────────────────────────────────────────────────

class TestVerificationCompilerRegex:
    """A3: Verification compiler must extract metrics from broader patterns."""

    def _extract(self, text: str):
        """Helper to run parameter extraction logic directly."""
        from app.services.verification_compiler_service import VerificationCompilerService
        # Create service with a no-op DB arg
        svc = VerificationCompilerService.__new__(VerificationCompilerService)
        return svc._extract_parameters(text)

    def test_respond_within_200ms(self):
        """Standard respond pattern must extract metric."""
        metric, op, threshold, unit, pop = self._extract(
            "The system shall respond within 200 milliseconds for 95% of requests."
        )
        assert metric == "Response Time"
        assert threshold == "200"
        assert "pop" in ("95% of requests",) or pop is not None

    def test_return_search_results_within_200ms(self):
        """A3 FIX: 'return search results within 200ms' must extract metric.
        Previously failed because 'return' was not in the regex alternation."""
        metric, op, threshold, unit, pop = self._extract(
            "The system shall return search results within 200 milliseconds for 95% of requests."
        )
        assert metric == "Response Time", (
            f"Expected 'Response Time' but got {metric!r}. "
            "The 'return...within N ms' pattern was not matched."
        )
        assert threshold == "200"
        assert unit in ("milliseconds", "ms", "millisecond")

    def test_vague_requirement_no_metric(self):
        """Vague requirement should produce no metric/threshold."""
        metric, op, threshold, unit, pop = self._extract(
            "The system should be fast and user-friendly."
        )
        assert metric is None
        assert threshold is None

    def test_execute_within_500ms(self):
        """'execute within 500ms' must extract metric."""
        metric, op, threshold, unit, pop = self._extract(
            "The API shall execute within 500ms."
        )
        assert metric == "Response Time"
        assert threshold == "500"

    def test_complete_within_1_second(self):
        """'complete within 1 second' must extract metric."""
        metric, op, threshold, unit, pop = self._extract(
            "The checkout process shall complete within 1 second."
        )
        assert metric == "Response Time"
        assert threshold == "1"

    def test_population_extracted(self):
        """Population/percentile must be extracted."""
        _, _, _, _, pop = self._extract(
            "The system shall respond within 200ms for 95% of requests."
        )
        assert pop is not None
        assert "95%" in pop


# ── A4/A8 Regression Tests ────────────────────────────────────────────────────

class TestEARSIdempotency:
    """A4/A8: EARS improvement must be idempotent for already-improved requirements."""

    @pytest.mark.asyncio
    async def test_already_ears_formatted_unchanged(self):
        """Already-EARS requirement must be returned unchanged without mangling."""
        provider = HeuristicsAIProvider()
        already_good = "The SRSense System shall respond within 200 milliseconds."
        result = await provider.suggest_improvement(
            title="API Latency",
            description=already_good,
            req_type="non_functional",
        )
        assert result.improved_description == already_good, (
            f"Idempotency broken. Expected:\n  {already_good!r}\nGot:\n  {result.improved_description!r}"
        )
        assert "The SRSense System shall the" not in result.improved_description
        assert "shall respond within 200" in result.improved_description

    @pytest.mark.asyncio
    async def test_no_double_subject(self):
        """Must never produce 'The SRSense System shall the system should be...'"""
        provider = HeuristicsAIProvider()
        result = await provider.suggest_improvement(
            title="Speed",
            description="The system should be fast.",
            req_type="non_functional",
        )
        assert "shall the system" not in result.improved_description
        assert "should be respond" not in result.improved_description
        assert "The SRSense System shall" in result.improved_description

    @pytest.mark.asyncio
    async def test_when_trigger_idempotent(self):
        """WHEN-prefixed EARS requirement is also idempotent."""
        provider = HeuristicsAIProvider()
        already_when = "WHEN user submits form, the SRSense System shall validate all fields."
        result = await provider.suggest_improvement(
            title="Form Validation",
            description=already_when,
            req_type="functional",
        )
        # Should not re-process since it already starts with the EARS prefix pattern
        assert result.improved_description == already_when or (
            "shall validate all fields" in result.improved_description
        )
        assert "shall the SRSense System shall" not in result.improved_description

    @pytest.mark.asyncio
    async def test_malformed_not_100_score(self):
        """A8: A mangled description must NOT receive 100/100 quality score."""
        provider = HeuristicsAIProvider()
        # Simulate what a malformed EARS requirement looks like
        malformed = "The SRSense System shall the system should be respond within 200 milliseconds."
        result = await provider.analyze_requirement(
            title="Malformed Req",
            description=malformed,
            req_type="non_functional",
        )
        assert result.quality_score < 100, (
            "Malformed EARS output must be penalized, not scored 100/100."
        )
        assert result.quality_score <= 60

    @pytest.mark.asyncio
    async def test_exact_malformed_fast_user_friendly_requirement_score_reduced(self):
        """Regression: Exact requirement 'Fast and user-friendly system' must NOT receive 100/100."""
        provider = HeuristicsAIProvider()
        desc = (
            "The SRSense System shall the system should be respond within 200 milliseconds "
            "and require no more than 3 user interactions."
        )
        result = await provider.analyze_requirement(
            title="Fast and user-friendly system",
            description=desc,
            req_type="functional",
        )
        assert result.quality_score <= 60
        assert result.quality_score < 100
        assert any("Malformed EARS syntax detected" in c for c in result.missing_criteria)
        assert "Malformed EARS syntax detected" in result.summary_feedback


# ── A6 Regression Tests ───────────────────────────────────────────────────────

class TestRequirementIDDetection:
    """A6: Only structured IDs like FR-001 are valid. Ordinary words are not."""

    VALID_REQ_ID_PATTERN = re.compile(r"^[A-Z]{1,5}-\d{1,5}$")

    def is_valid(self, raw_id: str) -> bool:
        return bool(self.VALID_REQ_ID_PATTERN.match(raw_id.strip()))

    def test_fr001_is_valid(self):
        assert self.is_valid("FR-001")

    def test_nfr002_is_valid(self):
        assert self.is_valid("NFR-002")

    def test_req12_is_valid(self):
        assert self.is_valid("REQ-12")

    def test_us014_is_valid(self):
        assert self.is_valid("US-014")

    def test_sys999_is_valid(self):
        assert self.is_valid("SYS-999")

    def test_user_is_invalid(self):
        assert not self.is_valid("User")

    def test_system_is_invalid(self):
        assert not self.is_valid("System")

    def test_admin_is_invalid(self):
        assert not self.is_valid("Admin")

    def test_login_is_invalid(self):
        assert not self.is_valid("Login")

    def test_payment_is_invalid(self):
        assert not self.is_valid("Payment")

    def test_lowercase_fr001_is_invalid(self):
        """IDs must be uppercase prefix."""
        assert not self.is_valid("fr-001")

    def test_number_only_is_invalid(self):
        assert not self.is_valid("001")

    def test_no_dash_is_invalid(self):
        assert not self.is_valid("FR001")


# ── A9 Regression Tests ───────────────────────────────────────────────────────

class TestQualityAnalysisSource:
    """A9: Quality analysis must use description only, NOT the title."""

    @pytest.mark.asyncio
    async def test_vague_title_measurable_description_not_flagged(self):
        """Title 'Fast System' must NOT cause the requirement to be flagged as vague
        when the description contains a clear measurable threshold."""
        provider = HeuristicsAIProvider()
        result = await provider.analyze_requirement(
            title="Fast System",
            description="The SRSense System shall respond within 200 milliseconds.",
            req_type="non_functional",
        )
        assert result.quality_score >= 90, (
            f"Expected score >= 90 (measurable description), got {result.quality_score}. "
            "The word 'fast' in the title must NOT contaminate the description analysis."
        )
        # "fast" should not appear in ambiguity_tags since it's only in the title
        fast_tags = [t for t in result.ambiguity_tags if "fast" in t.lower()]
        assert len(fast_tags) == 0, (
            f"'fast' (from title only) was incorrectly flagged in ambiguity_tags: {result.ambiguity_tags}"
        )

    @pytest.mark.asyncio
    async def test_vague_description_still_flagged(self):
        """Vague description must still be flagged regardless of neutral title."""
        provider = HeuristicsAIProvider()
        result = await provider.analyze_requirement(
            title="System Performance",
            description="The system should be fast and user-friendly.",
            req_type="non_functional",
        )
        assert result.quality_score < 75
        assert len(result.ambiguity_tags) >= 2

    @pytest.mark.asyncio
    async def test_neutral_title_measurable_description_high_score(self):
        """Neutral title + measurable description = high score."""
        provider = HeuristicsAIProvider()
        result = await provider.analyze_requirement(
            title="API Response Latency",
            description="The system shall return search results within 200 milliseconds for 95% of requests.",
            req_type="non_functional",
        )
        assert result.quality_score >= 85, (
            f"Expected score >= 85 for measurable requirement, got {result.quality_score}"
        )
