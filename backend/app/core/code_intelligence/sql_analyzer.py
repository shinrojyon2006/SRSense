"""
SQL AST Code Analyzer for Sprint 2.0.

Extracts tables, views, procedures, schemas, and query operations.
"""

import re
from typing import List, Dict, Any

from app.core.code_intelligence.base_analyzer import (
    BaseLanguageAnalyzer,
    ParsedFileResult,
    ParsedSymbol,
    ParsedDependency,
)


class SQLAnalyzer(BaseLanguageAnalyzer):
    """Analyzes SQL files for tables, views, procedures, and queries."""

    def analyze(
        self,
        rel_path: str,
        filename: str,
        content: str,
        language: str = "SQL",
        confidence: str = "High",
    ) -> ParsedFileResult:
        line_count = len(content.splitlines()) if content else 0
        size_bytes = len(content.encode("utf-8")) if content else 0

        symbols: List[ParsedSymbol] = []
        dependencies: List[ParsedDependency] = []
        db_interactions: List[Dict[str, Any]] = []

        lines = content.splitlines()

        CREATE_TABLE_PATTERN = re.compile(
            r"^\s*CREATE\s+(?:OR\s+REPLACE\s+)?(?:TEMPORARY\s+|TEMP\s+|UNLOGGED\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:[A-Za-z0-9_]+\.)?([A-Za-z0-9_\"`]+)",
            re.IGNORECASE,
        )
        CREATE_VIEW_PATTERN = re.compile(
            r"^\s*CREATE\s+(?:OR\s+REPLACE\s+)?(?:MATERIALIZED\s+)?VIEW\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:[A-Za-z0-9_]+\.)?([A-Za-z0-9_\"`]+)",
            re.IGNORECASE,
        )
        CREATE_PROC_PATTERN = re.compile(
            r"^\s*CREATE\s+(?:OR\s+REPLACE\s+)?(?:PROCEDURE|FUNCTION)\s+(?:[A-Za-z0-9_]+\.)?([A-Za-z0-9_\"`]+)",
            re.IGNORECASE,
        )
        FOREIGN_KEY_PATTERN = re.compile(
            r"REFERENCES\s+([A-Za-z0-9_]+)", re.IGNORECASE
        )

        for idx, line in enumerate(lines, start=1):
            line_str = line.strip()

            if line_str.startswith("--") or line_str.startswith("/*"):
                continue

            # Tables
            table_match = CREATE_TABLE_PATTERN.match(line_str)
            if table_match:
                t_name = table_match.group(1).strip("\"`")
                symbols.append(
                    ParsedSymbol(
                        symbol_name=t_name,
                        symbol_type="table",
                        line_start=idx,
                        signature=line_str,
                    )
                )
                continue

            # Views
            view_match = CREATE_VIEW_PATTERN.match(line_str)
            if view_match:
                v_name = view_match.group(1).strip("\"`")
                symbols.append(
                    ParsedSymbol(
                        symbol_name=v_name,
                        symbol_type="view",
                        line_start=idx,
                        signature=line_str,
                    )
                )
                continue

            # Procedures / Functions
            proc_match = CREATE_PROC_PATTERN.match(line_str)
            if proc_match:
                p_name = proc_match.group(1).strip("\"`")
                symbols.append(
                    ParsedSymbol(
                        symbol_name=p_name,
                        symbol_type="procedure",
                        line_start=idx,
                        signature=line_str,
                    )
                )
                continue

            # Table dependencies (FOREIGN KEY REFERENCES)
            fk_match = FOREIGN_KEY_PATTERN.search(line_str)
            if fk_match:
                ref_table = fk_match.group(1)
                dependencies.append(
                    ParsedDependency(target_module=ref_table, dependency_type="extends")
                )

            # Query interactions
            if re.match(r"^\s*(SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM|ALTER\s+TABLE|DROP\s+TABLE)\b", line_str, re.IGNORECASE):
                op_name = line_str.split()[0].upper()
                db_interactions.append({
                    "operation_type": f"SQL {op_name}",
                    "matched_code": line_str[:120],
                    "line_number": idx,
                })

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
            db_interactions=db_interactions,
            metadata_json={},
        )
