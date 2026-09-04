"""
Base classes and data contracts for Sprint 2.0 Code Intelligence Analyzers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ParsedSymbol:
    symbol_name: str
    symbol_type: str  # class, interface, struct, function, method, endpoint, table, view, procedure
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    signature: Optional[str] = None
    docstring: Optional[str] = None
    parent_symbol_name: Optional[str] = None
    metadata_json: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedDependency:
    target_module: str
    dependency_type: str = "imports"  # imports, includes, calls, extends


@dataclass
class ParsedFileResult:
    path: str
    filename: str
    language: str
    confidence: str
    line_count: int
    size_bytes: int
    symbols: List[ParsedSymbol] = field(default_factory=list)
    dependencies: List[ParsedDependency] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    endpoints: List[Dict[str, Any]] = field(default_factory=list)
    db_interactions: List[Dict[str, Any]] = field(default_factory=list)
    metadata_json: Dict[str, Any] = field(default_factory=dict)


class BaseLanguageAnalyzer(ABC):
    """Abstract base class for language AST analyzers."""

    @abstractmethod
    def analyze(
        self,
        rel_path: str,
        filename: str,
        content: str,
        language: str,
        confidence: str,
    ) -> ParsedFileResult:
        """Parse source code as static text and extract structured constructs."""
        pass
