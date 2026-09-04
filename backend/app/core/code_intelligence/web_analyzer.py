"""
HTML and CSS Code Analyzers for Sprint 2.0.

Extracts forms, script/link tags, CSS selectors, variables, and media queries.
"""

import re
from typing import List, Dict, Any

from app.core.code_intelligence.base_analyzer import (
    BaseLanguageAnalyzer,
    ParsedFileResult,
    ParsedSymbol,
    ParsedDependency,
)


class HTMLAnalyzer(BaseLanguageAnalyzer):
    """Analyzes HTML files for forms, script dependencies, and structural elements."""

    def analyze(
        self,
        rel_path: str,
        filename: str,
        content: str,
        language: str = "HTML",
        confidence: str = "High",
    ) -> ParsedFileResult:
        line_count = len(content.splitlines()) if content else 0
        size_bytes = len(content.encode("utf-8")) if content else 0

        symbols: List[ParsedSymbol] = []
        dependencies: List[ParsedDependency] = []
        endpoints: List[Dict[str, Any]] = []

        FORM_PATTERN = re.compile(r"<form\b([^>]*)>", re.IGNORECASE)
        ACTION_PATTERN = re.compile(r'action=["\']([^"\']+)["\']', re.IGNORECASE)
        METHOD_PATTERN = re.compile(r'method=["\']([^"\']+)["\']', re.IGNORECASE)
        SCRIPT_SRC_PATTERN = re.compile(r'<script\b[^>]*src=["\']([^"\']+)["\']', re.IGNORECASE)
        LINK_HREF_PATTERN = re.compile(r'<link\b[^>]*href=["\']([^"\']+)["\']', re.IGNORECASE)

        for idx, line in enumerate(content.splitlines(), start=1):
            line_str = line.strip()

            # Form elements as interaction endpoints
            form_match = FORM_PATTERN.search(line_str)
            if form_match:
                attrs = form_match.group(1)
                action = ACTION_PATTERN.search(attrs)
                method = METHOD_PATTERN.search(attrs)
                act_url = action.group(1) if action else "/"
                meth_val = method.group(1).upper() if method else "GET"

                endpoints.append({
                    "http_method": meth_val,
                    "path": act_url,
                    "line_number": idx,
                    "is_html_form": True,
                })
                symbols.append(
                    ParsedSymbol(
                        symbol_name=f"Form [{meth_val} {act_url}]",
                        symbol_type="endpoint",
                        line_start=idx,
                        signature=line_str[:100],
                    )
                )

            # Script dependencies
            script_match = SCRIPT_SRC_PATTERN.search(line_str)
            if script_match:
                dependencies.append(
                    ParsedDependency(target_module=script_match.group(1), dependency_type="includes")
                )

            # Stylesheet links
            link_match = LINK_HREF_PATTERN.search(line_str)
            if link_match:
                dependencies.append(
                    ParsedDependency(target_module=link_match.group(1), dependency_type="includes")
                )

        return ParsedFileResult(
            path=rel_path,
            filename=filename,
            language=language,
            confidence=confidence,
            line_count=line_count,
            size_bytes=size_bytes,
            symbols=symbols,
            dependencies=dependencies,
            imports=[],
            exports=[],
            endpoints=endpoints,
            db_interactions=[],
            metadata_json={},
        )


class CSSAnalyzer(BaseLanguageAnalyzer):
    """Analyzes CSS, SCSS, and Less files for selectors, rules, and media queries."""

    def analyze(
        self,
        rel_path: str,
        filename: str,
        content: str,
        language: str = "CSS",
        confidence: str = "High",
    ) -> ParsedFileResult:
        line_count = len(content.splitlines()) if content else 0
        size_bytes = len(content.encode("utf-8")) if content else 0

        symbols: List[ParsedSymbol] = []
        dependencies: List[ParsedDependency] = []

        IMPORT_PATTERN = re.compile(r'@import\s+(?:url\()?[\'"]([^\'")]+)[\'"]\)?;')
        SELECTOR_PATTERN = re.compile(r"^([.#]?[A-Za-z0-9_-]+(?:\s*,\s*[.#]?[A-Za-z0-9_-]+)*)\s*\{")
        MEDIA_PATTERN = re.compile(r"^@media\s+([^{]+)\{")

        for idx, line in enumerate(content.splitlines(), start=1):
            line_str = line.strip()

            # Imports
            imp_match = IMPORT_PATTERN.search(line_str)
            if imp_match:
                dependencies.append(
                    ParsedDependency(target_module=imp_match.group(1), dependency_type="imports")
                )
                continue

            # Media Queries
            media_match = MEDIA_PATTERN.match(line_str)
            if media_match:
                symbols.append(
                    ParsedSymbol(
                        symbol_name=f"@media {media_match.group(1).strip()}",
                        symbol_type="interface",
                        line_start=idx,
                        signature=line_str,
                    )
                )
                continue

            # Class/ID selectors
            sel_match = SELECTOR_PATTERN.match(line_str)
            if sel_match and not line_str.startswith("@") and not line_str.startswith("/*"):
                sel_name = sel_match.group(1).strip()
                if len(sel_name) <= 60:
                    symbols.append(
                        ParsedSymbol(
                            symbol_name=sel_name,
                            symbol_type="class",
                            line_start=idx,
                            signature=line_str,
                        )
                    )

        return ParsedFileResult(
            path=rel_path,
            filename=filename,
            language=language,
            confidence=confidence,
            line_count=line_count,
            size_bytes=size_bytes,
            symbols=symbols,
            dependencies=dependencies,
            imports=[],
            exports=[],
            endpoints=[],
            db_interactions=[],
            metadata_json={},
        )
