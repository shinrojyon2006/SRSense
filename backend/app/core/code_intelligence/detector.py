"""
Multi-signal programming language detector for Sprint 2.0.

Evaluates file extension, filename patterns, and syntax heuristics to classify
files into supported languages with confidence ratings.
"""

from dataclasses import dataclass
from enum import Enum
import os
import re
from typing import Optional


class LanguageConfidence(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    UNKNOWN = "Unknown"


@dataclass
class LanguageDetectionResult:
    language: str
    confidence: str
    is_supported: bool


class LanguageDetector:
    """Detects programming languages using extensions, names, and content."""

    # Explicit extension mappings
    EXTENSION_MAP = {
        # Python
        ".py": ("Python", LanguageConfidence.HIGH),
        ".pyi": ("Python", LanguageConfidence.HIGH),
        ".pyw": ("Python", LanguageConfidence.HIGH),
        # TypeScript / TSX
        ".ts": ("TypeScript", LanguageConfidence.HIGH),
        ".tsx": ("TypeScript", LanguageConfidence.HIGH),
        ".mts": ("TypeScript", LanguageConfidence.HIGH),
        ".cts": ("TypeScript", LanguageConfidence.HIGH),
        # JavaScript / JSX
        ".js": ("JavaScript", LanguageConfidence.HIGH),
        ".jsx": ("JavaScript", LanguageConfidence.HIGH),
        ".mjs": ("JavaScript", LanguageConfidence.HIGH),
        ".cjs": ("JavaScript", LanguageConfidence.HIGH),
        # Java
        ".java": ("Java", LanguageConfidence.HIGH),
        # C++
        ".cpp": ("C++", LanguageConfidence.HIGH),
        ".cc": ("C++", LanguageConfidence.HIGH),
        ".cxx": ("C++", LanguageConfidence.HIGH),
        ".hpp": ("C++", LanguageConfidence.HIGH),
        ".hxx": ("C++", LanguageConfidence.HIGH),
        ".c++": ("C++", LanguageConfidence.HIGH),
        ".h++": ("C++", LanguageConfidence.HIGH),
        # C
        ".c": ("C", LanguageConfidence.HIGH),
        # HTML
        ".html": ("HTML", LanguageConfidence.HIGH),
        ".htm": ("HTML", LanguageConfidence.HIGH),
        ".xhtml": ("HTML", LanguageConfidence.HIGH),
        # CSS
        ".css": ("CSS", LanguageConfidence.HIGH),
        ".scss": ("CSS", LanguageConfidence.HIGH),
        ".sass": ("CSS", LanguageConfidence.HIGH),
        ".less": ("CSS", LanguageConfidence.HIGH),
        # SQL
        ".sql": ("SQL", LanguageConfidence.HIGH),
        ".psql": ("SQL", LanguageConfidence.HIGH),
    }

    # Supported target language set
    SUPPORTED_LANGUAGES = {
        "Python",
        "C",
        "C++",
        "Java",
        "JavaScript",
        "TypeScript",
        "HTML",
        "CSS",
        "SQL",
    }

    @classmethod
    def detect(cls, filename: str, content: Optional[str] = None) -> LanguageDetectionResult:
        """Detect language for a file by path/name and optional content sample."""
        base_name = os.path.basename(filename).lower()
        _, ext = os.path.splitext(base_name)

        # 1. Disambiguate .h files (C vs C++)
        if ext == ".h":
            if content:
                # Check for C++ specific constructs in header
                cpp_indicators = [
                    r"\bclass\s+\w+",
                    r"\bnamespace\s+\w+",
                    r"\btemplate\s*<",
                    r"\bstd::",
                    r"\bpublic:",
                    r"\bprivate:",
                    r"\bprotected:",
                    r"#include\s+<(iostream|vector|string|memory|map|set|algorithm)>",
                ]
                if any(re.search(pat, content) for pat in cpp_indicators):
                    return LanguageDetectionResult(
                        language="C++",
                        confidence=LanguageConfidence.HIGH.value,
                        is_supported=True,
                    )
                else:
                    return LanguageDetectionResult(
                        language="C",
                        confidence=LanguageConfidence.MEDIUM.value,
                        is_supported=True,
                    )
            return LanguageDetectionResult(
                language="C",
                confidence=LanguageConfidence.MEDIUM.value,
                is_supported=True,
            )

        # 2. Match standard extension map
        if ext in cls.EXTENSION_MAP:
            lang, conf = cls.EXTENSION_MAP[ext]
            return LanguageDetectionResult(
                language=lang,
                confidence=conf.value,
                is_supported=True,
            )

        # 3. Content-based detection for files without recognized extension (e.g., shebang)
        if content:
            first_line = content.strip().split("\n")[0].lower() if content.strip() else ""
            if first_line.startswith("#!"):
                if "python" in first_line:
                    return LanguageDetectionResult(
                        language="Python",
                        confidence=LanguageConfidence.MEDIUM.value,
                        is_supported=True,
                    )
                if "node" in first_line:
                    return LanguageDetectionResult(
                        language="JavaScript",
                        confidence=LanguageConfidence.MEDIUM.value,
                        is_supported=True,
                    )

            # Detect HTML by DOCTYPE / <html>
            if re.search(r"<!doctype\s+html|<html\b", content[:500], re.IGNORECASE):
                return LanguageDetectionResult(
                    language="HTML",
                    confidence=LanguageConfidence.MEDIUM.value,
                    is_supported=True,
                )

        # 4. Unknown / Unsupported
        return LanguageDetectionResult(
            language="Unknown / Unsupported",
            confidence=LanguageConfidence.UNKNOWN.value,
            is_supported=False,
        )
