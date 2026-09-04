"""
Java AST Code Analyzer for Sprint 2.0.

Extracts packages, classes, interfaces, methods, Spring Boot / Jakarta REST
endpoints, annotations, imports, and database interactions.
"""

import re
from typing import List, Dict, Any, Optional

from app.core.code_intelligence.base_analyzer import (
    BaseLanguageAnalyzer,
    ParsedFileResult,
    ParsedSymbol,
    ParsedDependency,
)


class JavaAnalyzer(BaseLanguageAnalyzer):
    """Analyzes Java source code for structural elements."""

    def analyze(
        self,
        rel_path: str,
        filename: str,
        content: str,
        language: str = "Java",
        confidence: str = "High",
    ) -> ParsedFileResult:
        line_count = len(content.splitlines()) if content else 0
        size_bytes = len(content.encode("utf-8")) if content else 0

        symbols: List[ParsedSymbol] = []
        dependencies: List[ParsedDependency] = []
        imports_list: List[str] = []
        endpoints: List[Dict[str, Any]] = []
        db_interactions: List[Dict[str, Any]] = []

        lines = content.splitlines()

        # Regex patterns
        PACKAGE_PATTERN = re.compile(r"^\s*package\s+([A-Za-z0-9_.]+)\s*;")
        IMPORT_PATTERN = re.compile(r"^\s*import\s+(?:static\s+)?([A-Za-z0-9_.*]+)\s*;")
        CLASS_PATTERN = re.compile(
            r"^\s*(?:public|protected|private|abstract|final|static|\s)*\s*class\s+([A-Za-z0-9_$]+)(?:\s+extends\s+([A-Za-z0-9_$.]+))?(?:\s+implements\s+([A-Za-z0-9_$,\s]+))?"
        )
        INTERFACE_PATTERN = re.compile(
            r"^\s*(?:public|protected|private|abstract|\s)*\s*interface\s+([A-Za-z0-9_$]+)(?:\s+extends\s+([A-Za-z0-9_$,\s]+))?"
        )
        ENUM_PATTERN = re.compile(r"^\s*(?:public|protected|private|\s)*\s*enum\s+([A-Za-z0-9_$]+)")
        METHOD_PATTERN = re.compile(
            r"^\s*(?:public|protected|private|static|final|synchronized|abstract|\s)*\s*([A-Za-z0-9_<>[\]]+)\s+([A-Za-z0-9_$]+)\s*\((.*?)\)(?:\s+throws\s+[A-Za-z0-9_$,\s]+)?\s*[{;]"
        )
        SPRING_ENDPOINT_PATTERN = re.compile(
            r"@(Get|Post|Put|Delete|Patch|Request)Mapping\s*(?:\(\s*(?:value\s*=\s*|path\s*=\s*)?['\"]([^'\"]+)['\"]|\(\s*['\"]([^'\"]+)['\"])?",
            re.IGNORECASE,
        )

        package_name = ""
        current_class: Optional[str] = None
        pending_annotations: List[str] = []

        for idx, line in enumerate(lines, start=1):
            line_str = line.strip()

            if line_str.startswith("//") or line_str.startswith("/*") or line_str.startswith("*"):
                continue

            # Package
            pkg_match = PACKAGE_PATTERN.match(line_str)
            if pkg_match:
                package_name = pkg_match.group(1)
                continue

            # Imports
            imp_match = IMPORT_PATTERN.match(line_str)
            if imp_match:
                imported_pkg = imp_match.group(1)
                imports_list.append(line_str)
                dependencies.append(
                    ParsedDependency(target_module=imported_pkg, dependency_type="imports")
                )
                continue

            # Annotations (e.g. @Override, @GetMapping("/users"), @Autowired)
            if line_str.startswith("@"):
                pending_annotations.append(line_str)
                # Check Spring Route
                ep_match = SPRING_ENDPOINT_PATTERN.search(line_str)
                if ep_match:
                    method_type = ep_match.group(1).upper()
                    ep_path = ep_match.group(2) or ep_match.group(3) or "/"
                    endpoints.append({
                        "http_method": method_type if method_type != "REQUEST" else "ANY",
                        "path": ep_path,
                        "line_number": idx,
                    })
                    symbols.append(
                        ParsedSymbol(
                            symbol_name=f"{method_type} {ep_path}",
                            symbol_type="endpoint",
                            line_start=idx,
                            signature=line_str,
                            metadata_json={"framework": "Spring Boot"},
                        )
                    )
                continue

            # Class definition
            cls_match = CLASS_PATTERN.match(line_str)
            if cls_match:
                cls_name = cls_match.group(1)
                current_class = cls_name
                extends_cls = cls_match.group(2)
                symbols.append(
                    ParsedSymbol(
                        symbol_name=cls_name,
                        symbol_type="class",
                        line_start=idx,
                        signature=line_str,
                        metadata_json={
                            "package": package_name,
                            "extends": extends_cls,
                            "implements": cls_match.group(3),
                            "annotations": list(pending_annotations),
                        },
                    )
                )
                if extends_cls:
                    dependencies.append(
                        ParsedDependency(target_module=extends_cls, dependency_type="extends")
                    )
                pending_annotations.clear()
                continue

            # Interface definition
            iface_match = INTERFACE_PATTERN.match(line_str)
            if iface_match:
                iface_name = iface_match.group(1)
                symbols.append(
                    ParsedSymbol(
                        symbol_name=iface_name,
                        symbol_type="interface",
                        line_start=idx,
                        signature=line_str,
                        metadata_json={
                            "package": package_name,
                            "extends": iface_match.group(2),
                            "annotations": list(pending_annotations),
                        },
                    )
                )
                pending_annotations.clear()
                continue

            # Enum definition
            enum_match = ENUM_PATTERN.match(line_str)
            if enum_match:
                symbols.append(
                    ParsedSymbol(
                        symbol_name=enum_match.group(1),
                        symbol_type="class",
                        line_start=idx,
                        signature=line_str,
                        metadata_json={"is_enum": True, "package": package_name},
                    )
                )
                pending_annotations.clear()
                continue

            # Methods
            method_match = METHOD_PATTERN.match(line_str)
            if method_match:
                ret_type = method_match.group(1)
                method_name = method_match.group(2)
                if method_name not in ("if", "for", "while", "switch", "catch", "return"):
                    symbols.append(
                        ParsedSymbol(
                            symbol_name=method_name,
                            symbol_type="method" if current_class else "function",
                            line_start=idx,
                            signature=line_str,
                            parent_symbol_name=current_class,
                            metadata_json={
                                "return_type": ret_type,
                                "annotations": list(pending_annotations),
                            },
                        )
                    )
                pending_annotations.clear()
                continue

            # Reset annotations if normal statement reached
            if not line_str.startswith("@"):
                pending_annotations.clear()

            # Database / JPA queries
            if any(w in line_str for w in ("JpaRepository", "EntityManager", "createQuery", "SELECT ", "INSERT INTO ", "@Query")):
                db_interactions.append({
                    "operation_type": "Java/JPA Query",
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
            exports=[],
            endpoints=endpoints,
            db_interactions=db_interactions,
            metadata_json={"package": package_name},
        )
