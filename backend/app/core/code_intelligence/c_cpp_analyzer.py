"""
C and C++ AST Code Analyzer for Sprint 2.0.

Extracts structs, classes, functions, and #include directives.
"""

import re
from typing import List, Dict, Any, Optional

from app.core.code_intelligence.base_analyzer import (
    BaseLanguageAnalyzer,
    ParsedFileResult,
    ParsedSymbol,
    ParsedDependency,
)


class CCppAnalyzer(BaseLanguageAnalyzer):
    """Analyzes C and C++ source and header files."""

    def analyze(
        self,
        rel_path: str,
        filename: str,
        content: str,
        language: str = "C++",
        confidence: str = "High",
    ) -> ParsedFileResult:
        line_count = len(content.splitlines()) if content else 0
        size_bytes = len(content.encode("utf-8")) if content else 0

        symbols: List[ParsedSymbol] = []
        dependencies: List[ParsedDependency] = []
        includes_list: List[str] = []

        lines = content.splitlines()

        # Regex patterns
        INCLUDE_PATTERN = re.compile(r'^\s*#include\s+([<"][^>"]+[>"])')
        CLASS_PATTERN = re.compile(
            r"^\s*(?:template\s*<.*?>\s*)?(?:class|struct)\s+([A-Za-z0-9_$]+)(?:\s*:\s*(?:public|protected|private)\s+([A-Za-z0-9_$:<>]+))?"
        )
        STRUCT_TYPEDEF_PATTERN = re.compile(r"^\s*typedef\s+struct\s+([A-Za-z0-9_$]+)?")
        FUNC_PATTERN = re.compile(
            r"^\s*(?:inline|static|virtual|extern|\s)*\s*([A-Za-z0-9_*&:<>]+)\s+([A-Za-z0-9_$]+)\s*\((.*?)\)(?:\s*const)?\s*[{;]"
        )

        current_class: Optional[str] = None

        for idx, line in enumerate(lines, start=1):
            line_str = line.strip()

            if line_str.startswith("//") or line_str.startswith("/*") or line_str.startswith("*"):
                continue

            # Includes
            inc_match = INCLUDE_PATTERN.match(line_str)
            if inc_match:
                header = inc_match.group(1).strip('<">')
                includes_list.append(line_str)
                dependencies.append(
                    ParsedDependency(target_module=header, dependency_type="includes")
                )
                continue

            # Classes and Structs
            cls_match = CLASS_PATTERN.match(line_str)
            if cls_match:
                tag = "class" if "class " in line_str else "struct"
                name = cls_match.group(1)
                inherits = cls_match.group(2)
                current_class = name
                symbols.append(
                    ParsedSymbol(
                        symbol_name=name,
                        symbol_type=tag,
                        line_start=idx,
                        signature=line_str,
                        metadata_json={"inherits": inherits},
                    )
                )
                if inherits:
                    dependencies.append(
                        ParsedDependency(target_module=inherits, dependency_type="extends")
                    )
                continue

            # Functions
            fn_match = FUNC_PATTERN.match(line_str)
            if fn_match:
                ret = fn_match.group(1)
                fn_name = fn_match.group(2)
                if fn_name not in ("if", "for", "while", "switch", "catch", "return", "sizeof"):
                    symbols.append(
                        ParsedSymbol(
                            symbol_name=fn_name,
                            symbol_type="method" if current_class else "function",
                            line_start=idx,
                            signature=line_str,
                            parent_symbol_name=current_class,
                            metadata_json={"return_type": ret},
                        )
                    )
                continue

        return ParsedFileResult(
            path=rel_path,
            filename=filename,
            language=language,
            confidence=confidence,
            line_count=line_count,
            size_bytes=size_bytes,
            symbols=symbols,
            dependencies=dependencies,
            imports=includes_list,
            exports=[],
            endpoints=[],
            db_interactions=[],
            metadata_json={"has_templates": "template<" in content},
        )
