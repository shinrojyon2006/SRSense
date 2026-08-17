"""
Abstract AI Provider Interface.

Defines standard provider contracts for requirement quality scoring,
ambiguity detection, and EARS improvement suggestions.
"""

from abc import ABC, abstractmethod
from typing import List
from pydantic import BaseModel


class AnalysisResult(BaseModel):
    """Structured AI requirement analysis result."""

    quality_score: int
    ambiguity_tags: List[str]
    passive_voice_instances: List[str]
    missing_criteria: List[str]
    summary_feedback: str


class ImprovementResult(BaseModel):
    """Structured AI requirement improvement suggestion result."""

    improved_title: str
    improved_description: str
    ears_template_used: str
    explanation: str


class BaseAIProvider(ABC):
    """Abstract interface for AI analysis providers."""

    @abstractmethod
    async def analyze_requirement(
        self, title: str, description: str, req_type: str
    ) -> AnalysisResult:
        """Analyze a requirement for ambiguity, quality score, and completeness."""
        pass

    @abstractmethod
    async def suggest_improvement(
        self, title: str, description: str, req_type: str
    ) -> ImprovementResult:
        """Generate an improved EARS-formatted requirement specification draft."""
        pass
