"""
Python AST Code Analyzer for Sprint 2.0.

Extracts classes, functions, async methods, decorators, imports,
FastAPI/Flask API endpoints, and SQLAlchemy database operations safely.
"""

import ast
import re
from typing import List, Dict, Any, Optional

from app.core.code_intelligence.base_analyzer import (
    BaseLanguageAnalyzer,
    ParsedFileResult,
    ParsedSymbol,
    ParsedDependency,
)


class PythonAnalyzer(BaseLanguageAnalyzer):
    """Parses Python source code using the standard library `ast` module."""

    def analyze(
        self,
        rel_path: str,
        filename: str,
        content: str,
        language: str = "Python",
        confidence: str = "High",
    ) -> ParsedFileResult:
        line_count = len(content.splitlines()) if content else 0
        size_bytes = len(content.encode("utf-8")) if content else 0

        symbols: List[ParsedSymbol] = []
        dependencies: List[ParsedDependency] = []
        imports_list: List[str] = []
        endpoints: List[Dict[str, Any]] = []
        db_interactions: List[Dict[str, Any]] = []

        try:
            tree = ast.parse(content, filename=filename)
        except (SyntaxError, ValueError, Exception):
            # Fallback to regex-based extraction if syntax has Python version variance
            return self._fallback_regex_analysis(
                rel_path, filename, content, language, confidence, line_count, size_bytes
            )

        # 1. Traverse AST for Imports & Dependencies
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports_list.append(alias.name)
                    dependencies.append(
                        ParsedDependency(target_module=alias.name, dependency_type="imports")
                    )
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                names = ", ".join(a.name for a in node.names)
                full_import = f"from {mod} import {names}" if mod else f"import {names}"
                imports_list.append(full_import)
                if mod:
                    dependencies.append(
                        ParsedDependency(target_module=mod, dependency_type="imports")
                    )

        # 2. Extract Top-level & Class-level symbols
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node)
                bases = [self._format_node(b) for b in node.bases]
                class_sym = ParsedSymbol(
                    symbol_name=node.name,
                    symbol_type="class",
                    line_start=node.lineno,
                    line_end=getattr(node, "end_lineno", node.lineno),
                    signature=f"class {node.name}({', '.join(bases)})" if bases else f"class {node.name}",
                    docstring=doc,
                    metadata_json={"bases": bases},
                )
                symbols.append(class_sym)

                # Class methods
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_doc = ast.get_docstring(item)
                        sig = self._format_func_signature(item)
                        decorators = [self._format_node(d) for d in item.decorator_list]
                        is_async = isinstance(item, ast.AsyncFunctionDef)

                        sym = ParsedSymbol(
                            symbol_name=item.name,
                            symbol_type="method",
                            line_start=item.lineno,
                            line_end=getattr(item, "end_lineno", item.lineno),
                            signature=sig,
                            docstring=method_doc,
                            parent_symbol_name=node.name,
                            metadata_json={
                                "is_async": is_async,
                                "decorators": decorators,
                            },
                        )
                        symbols.append(sym)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_doc = ast.get_docstring(node)
                sig = self._format_func_signature(node)
                decorators = [self._format_node(d) for d in node.decorator_list]
                is_async = isinstance(node, ast.AsyncFunctionDef)

                func_sym = ParsedSymbol(
                    symbol_name=node.name,
                    symbol_type="function",
                    line_start=node.lineno,
                    line_end=getattr(node, "end_lineno", node.lineno),
                    signature=sig,
                    docstring=func_doc,
                    metadata_json={
                        "is_async": is_async,
                        "decorators": decorators,
                    },
                )
                symbols.append(func_sym)

                # Check if this function is an API route endpoint
                endpoint_info = self._extract_endpoint(node, decorators)
                if endpoint_info:
                    endpoints.append(endpoint_info)
                    symbols.append(
                        ParsedSymbol(
                            symbol_name=f"{endpoint_info['http_method']} {endpoint_info['path']}",
                            symbol_type="endpoint",
                            line_start=node.lineno,
                            line_end=getattr(node, "end_lineno", node.lineno),
                            signature=f"{endpoint_info['http_method']} {endpoint_info['path']}",
                            parent_symbol_name=node.name,
                            metadata_json=endpoint_info,
                        )
                    )

        # 3. Detect Database Operations
        db_interactions = self._detect_db_operations(content)

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
            metadata_json={"ast_parsed": True},
        )

    def _format_func_signature(self, node: ast.AST) -> str:
        """Construct human-readable signature string."""
        prefix = "async def " if isinstance(node, ast.AsyncFunctionDef) else "def "
        args_list = []
        args_obj = getattr(node, "args", None)
        if args_obj:
            for a in args_obj.args:
                arg_name = a.arg
                if a.annotation:
                    arg_name += f": {self._format_node(a.annotation)}"
                args_list.append(arg_name)
        ret = f" -> {self._format_node(node.returns)}" if getattr(node, "returns", None) else ""
        return f"{prefix}{node.name}({', '.join(args_list)}){ret}"

    def _format_node(self, node: Optional[ast.AST]) -> str:
        if node is None:
            return ""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{self._format_node(node.value)}.{node.attr}"
        if isinstance(node, ast.Constant):
            return repr(node.value)
        if isinstance(node, ast.Call):
            func_name = self._format_node(node.func)
            args_str = ", ".join(self._format_node(a) for a in node.args)
            return f"{func_name}({args_str})"
        return getattr(node, "id", "") or getattr(node, "attr", "") or ""

    def _extract_endpoint(
        self, node: ast.AST, decorators: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Identify FastAPI / Flask route decorators."""
        for dec in decorators:
            # Matches @app.get('/path'), @router.post("/items"), @api.delete(...)
            match = re.search(
                r"(?:app|router|api|blueprint|bp)\.(get|post|put|delete|patch|options|head)\s*\(\s*['\"]([^'\"]+)['\"]",
                dec,
                re.IGNORECASE,
            )
            if match:
                return {
                    "http_method": match.group(1).upper(),
                    "path": match.group(2),
                    "handler_function": getattr(node, "name", ""),
                    "line_number": getattr(node, "lineno", None),
                }
            # Flask @app.route('/path', methods=['GET', 'POST'])
            flask_match = re.search(
                r"(?:app|bp)\.route\s*\(\s*['\"]([^'\"]+)['\"](?:.*methods\s*=\s*\[(.*?)\])?",
                dec,
                re.IGNORECASE,
            )
            if flask_match:
                path = flask_match.group(1)
                methods = flask_match.group(2) or "'GET'"
                methods_clean = [m.strip(" '\"") for m in methods.split(",") if m.strip()]
                return {
                    "http_method": "/".join(methods_clean) if methods_clean else "GET",
                    "path": path,
                    "handler_function": getattr(node, "name", ""),
                    "line_number": getattr(node, "lineno", None),
                }
        return None

    def _detect_db_operations(self, content: str) -> List[Dict[str, Any]]:
        """Detect SQLAlchemy and database queries."""
        interactions = []
        db_patterns = [
            (r"\b(session|db)\.(execute|query|add|commit|delete|flush|rollback)\s*\(", "SQLAlchemy ORM Call"),
            (r"\bselect\s*\(\s*([A-Z]\w+)", "SQLAlchemy Select Query"),
            (r"\b(SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+['\"]?\w+", "SQL Statement"),
            (r"\b([A-Z]\w+)\.objects\.(filter|get|create|all|update|delete)\s*\(", "Django ORM Call"),
        ]
        for line_idx, line in enumerate(content.splitlines(), start=1):
            for pat, desc in db_patterns:
                match = re.search(pat, line, re.IGNORECASE)
                if match:
                    interactions.append({
                        "operation_type": desc,
                        "matched_code": line.strip()[:120],
                        "line_number": line_idx,
                    })
                    break
        return interactions

    def _fallback_regex_analysis(
        self,
        rel_path: str,
        filename: str,
        content: str,
        language: str,
        confidence: str,
        line_count: int,
        size_bytes: int,
    ) -> ParsedFileResult:
        symbols: List[ParsedSymbol] = []
        imports_list: List[str] = []
        dependencies: List[ParsedDependency] = []

        lines = content.splitlines()
        for idx, line in enumerate(lines, start=1):
            line_str = line.strip()
            # Class match
            cls_match = re.match(r"^class\s+([A-Za-z0-9_]+)", line_str)
            if cls_match:
                symbols.append(
                    ParsedSymbol(
                        symbol_name=cls_match.group(1),
                        symbol_type="class",
                        line_start=idx,
                        signature=line_str,
                    )
                )
            # Function match
            fn_match = re.match(r"^(?:async\s+)?def\s+([A-Za-z0-9_]+)", line_str)
            if fn_match:
                symbols.append(
                    ParsedSymbol(
                        symbol_name=fn_match.group(1),
                        symbol_type="function",
                        line_start=idx,
                        signature=line_str,
                    )
                )
            # Import match
            if line_str.startswith("import ") or line_str.startswith("from "):
                imports_list.append(line_str)
                mod_match = re.match(r"^(?:from|import)\s+([A-Za-z0-9_\.]+)", line_str)
                if mod_match:
                    dependencies.append(
                        ParsedDependency(target_module=mod_match.group(1), dependency_type="imports")
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
            imports=imports_list,
            exports=[],
            endpoints=[],
            db_interactions=self._detect_db_operations(content),
            metadata_json={"ast_parsed": False},
        )
