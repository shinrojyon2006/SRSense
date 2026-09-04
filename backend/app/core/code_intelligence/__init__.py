"""
SRSense Code Intelligence Engine (Sprint 2.0).

Provides language detection, AST code analysis, dependency extraction,
and secure codebase ingestion.
"""

from app.core.code_intelligence.detector import LanguageDetector, LanguageDetectionResult
from app.core.code_intelligence.base_analyzer import (
    BaseLanguageAnalyzer,
    ParsedSymbol,
    ParsedDependency,
    ParsedFileResult,
)
from app.core.code_intelligence.factory import CodeAnalyzerFactory
from app.core.code_intelligence.ingestion import CodebaseIngestionEngine

__all__ = [
    "LanguageDetector",
    "LanguageDetectionResult",
    "BaseLanguageAnalyzer",
    "ParsedSymbol",
    "ParsedDependency",
    "ParsedFileResult",
    "CodeAnalyzerFactory",
    "CodebaseIngestionEngine",
]
