"""
TypeScript & JavaScript AST Code Analyzer for Sprint 2.0.

Extracts classes, interfaces, types, functions, methods, React hooks,
imports, exports, Express/fetch API endpoints, and database interactions.
"""

import re
from typing import List, Dict, Any

from app.core.code_intelligence.base_analyzer import (
    BaseLanguageAnalyzer,
    ParsedFileResult,
    ParsedSymbol,
    ParsedDependency,
)


class TypeScriptAnalyzer(BaseLanguageAnalyzer):
    """Analyzes TypeScript and JavaScript source code."""

    def analyze(
        self,
        rel_path: str,
        filename: str,
        content: str,
        language: str = "TypeScript",
        confidence: str = "High",
    ) -> ParsedFileResult:
        line_count = len(content.splitlines()) if content else 0
        size_bytes = len(content.encode("utf-8")) if content else 0

        symbols: List[ParsedSymbol] = []
        dependencies: List[ParsedDependency] = []
        imports_list: List[str] = []
        exports_list: List[str] = []
        endpoints: List[Dict[str, Any]] = []
        db_interactions: List[Dict[str, Any]] = []

        lines = content.splitlines()

        # 1. Regex patterns for symbols
        CLASS_PATTERN = re.compile(
            r"^(?:export\s+)?(?:abstract\s+)?class\s+([A-Za-z0-9_$]+)(?:\s+extends\s+([A-Za-z0-9_$.]+))?(?:\s+implements\s+([A-Za-z0-9_$,\s]+))?"
        )
        INTERFACE_PATTERN = re.compile(
            r"^(?:export\s+)?interface\s+([A-Za-z0-9_$]+)(?:\s+extends\s+([A-Za-z0-9_$,\s]+))?"
        )
        TYPE_PATTERN = re.compile(r"^(?:export\s+)?type\s+([A-Za-z0-9_$]+)\s*=")
        FUNC_PATTERN = re.compile(
            r"^(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\((.*?)\)"
        )
        ARROW_FUNC_PATTERN = re.compile(
            r"^(?:export\s+)?(?:const|let|var)\s+([A-Za-z0-9_$]+)\s*=\s*(?:async\s*)?(?:\((.*?)\)|[A-Za-z0-9_$]+)\s*=>"
        )
        REACT_COMPONENT_PATTERN = re.compile(
            r"^(?:export\s+)?(?:const|let|var)\s+([A-Z][A-Za-z0-9_$]*)\s*:\s*React\.FC"
        )

        # 2. Imports and Dependencies
        IMPORT_PATTERN = re.compile(
            r"^\s*(?:import\s+(?:.*?from\s+)?['\"]([^'\"]+)['\"]|const\s+.*?=\s*require\(['\"]([^'\"]+)['\"]\)|import\s*\(['\"]([^'\"]+)['\"]\)|import\s+['\"]([^'\"]+)['\"])",
            re.DOTALL,
        )

        # 3. Express / API Endpoints
        EXPRESS_ROUTE_PATTERN = re.compile(
            r"\b(?:app|router|server)\.(get|post|put|delete|patch|options|use)\s*\(\s*['\"]([^'\"]+)['\"]",
            re.IGNORECASE,
        )
        FETCH_CALL_PATTERN = re.compile(
            r"\b(?:fetch|axios\.(get|post|put|delete|patch))\s*\(\s*['\"]([^'\"]+)['\"]",
            re.IGNORECASE,
        )

        # 4. Database operations
        DB_PATTERN = re.compile(
            r"\b(?:prisma\.[a-zA-Z0-9_]+\.(?:findMany|findUnique|findFirst|create|update|delete)|mongoose\.model|sequelize\.query|db\.collection|knex\(['\"][a-zA-Z0-9_]+['\"]\))\b"
        )

        current_class: Optional[str] = None

        for idx, line in enumerate(lines, start=1):
            line_str = line.strip()

            # Skip pure comments
            if line_str.startswith("//") or line_str.startswith("/*") or line_str.startswith("*"):
                continue

            # Imports
            imp_match = IMPORT_PATTERN.match(line_str)
            if imp_match:
                mod_target = imp_match.group(1) or imp_match.group(2) or ""
                imports_list.append(line_str)
                if mod_target:
                    dependencies.append(
                        ParsedDependency(target_module=mod_target, dependency_type="imports")
                    )

            # Exports
            if line_str.startswith("export "):
                exports_list.append(line_str)

            # Classes
            cls_match = CLASS_PATTERN.match(line_str)
            if cls_match:
                cls_name = cls_match.group(1)
                extends_name = cls_match.group(2)
                current_class = cls_name
                symbols.append(
                    ParsedSymbol(
                        symbol_name=cls_name,
                        symbol_type="class",
                        line_start=idx,
                        signature=line_str,
                        metadata_json={
                            "extends": extends_name,
                            "implements": cls_match.group(3),
                        },
                    )
                )
                if extends_name:
                    dependencies.append(
                        ParsedDependency(target_module=extends_name, dependency_type="extends")
                    )
                continue

            # Interfaces
            iface_match = INTERFACE_PATTERN.match(line_str)
            if iface_match:
                iface_name = iface_match.group(1)
                symbols.append(
                    ParsedSymbol(
                        symbol_name=iface_name,
                        symbol_type="interface",
                        line_start=idx,
                        signature=line_str,
                        metadata_json={"extends": iface_match.group(2)},
                    )
                )
                continue

            # Types
            type_match = TYPE_PATTERN.match(line_str)
            if type_match:
                symbols.append(
                    ParsedSymbol(
                        symbol_name=type_match.group(1),
                        symbol_type="interface",
                        line_start=idx,
                        signature=line_str,
                    )
                )
                continue

            # React Component
            rc_match = REACT_COMPONENT_PATTERN.match(line_str)
            if rc_match:
                symbols.append(
                    ParsedSymbol(
                        symbol_name=rc_match.group(1),
                        symbol_type="function",
                        line_start=idx,
                        signature=line_str,
                        metadata_json={"is_react_component": True},
                    )
                )
                continue

            # Functions
            fn_match = FUNC_PATTERN.match(line_str)
            if fn_match:
                symbols.append(
                    ParsedSymbol(
                        symbol_name=fn_match.group(1),
                        symbol_type="function",
                        line_start=idx,
                        signature=line_str,
                    )
                )
                continue

            # Arrow Functions
            arrow_match = ARROW_FUNC_PATTERN.match(line_str)
            if arrow_match:
                symbols.append(
                    ParsedSymbol(
                        symbol_name=arrow_match.group(1),
                        symbol_type="function",
                        line_start=idx,
                        signature=line_str,
                    )
                )
                continue

            # Methods inside class (e.g., async fetchData() { or public getName(): string {)
            if current_class and re.match(r"^(?:public|private|protected|async|static|\s*)\s*([A-Za-z0-9_$]+)\s*\((.*?)\)", line_str):
                method_match = re.match(r"^(?:public|private|protected|async|static|\s*)*\s*([A-Za-z0-9_$]+)\s*\(", line_str)
                if method_match and method_match.group(1) not in ("if", "for", "while", "switch", "catch"):
                    symbols.append(
                        ParsedSymbol(
                            symbol_name=method_match.group(1),
                            symbol_type="method",
                            line_start=idx,
                            signature=line_str,
                            parent_symbol_name=current_class,
                        )
                    )

            # Express Routes
            route_match = EXPRESS_ROUTE_PATTERN.search(line_str)
            if route_match:
                http_m = route_match.group(1).upper()
                route_p = route_match.group(2)
                endpoints.append({
                    "http_method": http_m,
                    "path": route_p,
                    "line_number": idx,
                })
                symbols.append(
                    ParsedSymbol(
                        symbol_name=f"{http_m} {route_p}",
                        symbol_type="endpoint",
                        line_start=idx,
                        signature=f"{http_m} {route_p}",
                        metadata_json={"framework": "Express"},
                    )
                )

            # Fetch / Axios Calls
            fetch_match = FETCH_CALL_PATTERN.search(line_str)
            if fetch_match:
                m = (fetch_match.group(1) or "GET").upper()
                p = fetch_match.group(2)
                endpoints.append({
                    "http_method": m,
                    "path": p,
                    "line_number": idx,
                    "client_call": True,
                })

            # DB Queries
            if DB_PATTERN.search(line_str):
                db_interactions.append({
                    "operation_type": "Node/JS Database Call",
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
            imports=imports_list,
            exports=exports_list,
            endpoints=endpoints,
            db_interactions=db_interactions,
            metadata_json={"frameworks": ["React", "TypeScript"] if "tsx" in filename or "react" in content.lower() else ["TypeScript"]},
        )
