"""
Analyzer Factory for Sprint 2.0 Code Intelligence.

Dispatches language analyzers based on detected programming language.
"""

from typing import Dict, Type

from app.core.code_intelligence.base_analyzer import (
    BaseLanguageAnalyzer,
    ParsedFileResult,
)
from app.core.code_intelligence.python_analyzer import PythonAnalyzer
from app.core.code_intelligence.typescript_analyzer import TypeScriptAnalyzer
from app.core.code_intelligence.java_analyzer import JavaAnalyzer
from app.core.code_intelligence.c_cpp_analyzer import CCppAnalyzer
from app.core.code_intelligence.sql_analyzer import SQLAnalyzer
from app.core.code_intelligence.web_analyzer import HTMLAnalyzer, CSSAnalyzer


class GenericAnalyzer(BaseLanguageAnalyzer):
    """Fallback analyzer for unknown or unsupported file types."""

    def analyze(
        self,
        rel_path: str,
        filename: str,
        content: str,
        language: str = "Unknown / Unsupported",
        confidence: str = "Unknown",
    ) -> ParsedFileResult:
        line_count = len(content.splitlines()) if content else 0
        size_bytes = len(content.encode("utf-8")) if content else 0

        return ParsedFileResult(
            path=rel_path,
            filename=filename,
            language=language,
            confidence=confidence,
            line_count=line_count,
            size_bytes=size_bytes,
            symbols=[],
            dependencies=[],
            imports=[],
            exports=[],
            endpoints=[],
            db_interactions=[],
            metadata_json={"supported": False},
        )


class CodeAnalyzerFactory:
    """Factory to retrieve language analyzers."""

    _ANALYZERS: Dict[str, BaseLanguageAnalyzer] = {
        "Python": PythonAnalyzer(),
        "TypeScript": TypeScriptAnalyzer(),
        "JavaScript": TypeScriptAnalyzer(),
        "Java": JavaAnalyzer(),
        "C": CCppAnalyzer(),
        "C++": CCppAnalyzer(),
        "SQL": SQLAnalyzer(),
        "HTML": HTMLAnalyzer(),
        "CSS": CSSAnalyzer(),
    }

    _GENERIC_ANALYZER = GenericAnalyzer()

    @classmethod
    def get_analyzer(cls, language: str) -> BaseLanguageAnalyzer:
        """Return the analyzer for the given language or generic fallback."""
        return cls._ANALYZERS.get(language, cls._GENERIC_ANALYZER)
