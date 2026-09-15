"""
Test Discovery Engine for Sprint 2.4 Traceability.

Discovers test files and test functions across Python, JavaScript/TypeScript, Java,
and C/C++ deterministically without requiring test execution.
"""

import hashlib
import re
from typing import Dict, Any, List, Optional
from app.models.codebase import CodeFile
from app.models.traceability import TestType


class RawTestArtifact:
    """In-memory structure representing a discovered test function/file."""

    def __init__(
        self,
        file_path: str,
        test_name: str,
        test_framework: Optional[str] = None,
        test_type: str = TestType.UNIT.value,
        line_start: Optional[int] = None,
        line_end: Optional[int] = None,
        file_id: Optional[Any] = None,
        content_hash: Optional[str] = None,
    ):
        self.file_path = file_path
        self.test_name = test_name
        self.test_framework = test_framework
        self.test_type = test_type
        self.line_start = line_start
        self.line_end = line_end
        self.file_id = file_id
        self.content_hash = content_hash or hashlib.sha256(f"{file_path}:{test_name}:{line_start}".encode()).hexdigest()[:16]


class TestDiscoveryEngine:
    """Multi-language static test discovery engine."""

    @staticmethod
    def discover_tests(files: List[CodeFile]) -> List[RawTestArtifact]:
        """Scans codebase files and extracts test artifacts deterministically."""
        discovered: List[RawTestArtifact] = []

        for file in files:
            path_lower = file.path.lower()
            filename_lower = file.filename.lower()
            metadata = file.metadata_json or {}
            raw_content = metadata.get("raw_content", "")

            # Identify if file is a test file by path convention or content signals
            is_test_file = TestDiscoveryEngine._is_test_file(path_lower, filename_lower, raw_content)
            if not is_test_file:
                continue

            lang = (file.language or "").lower()

            if "python" in lang or filename_lower.endswith(".py"):
                file_tests = TestDiscoveryEngine._discover_python_tests(file, raw_content)
                discovered.extend(file_tests)
            elif any(ext in filename_lower for ext in [".ts", ".tsx", ".js", ".jsx"]):
                file_tests = TestDiscoveryEngine._discover_jsts_tests(file, raw_content)
                discovered.extend(file_tests)
            elif "java" in lang or filename_lower.endswith(".java"):
                file_tests = TestDiscoveryEngine._discover_java_tests(file, raw_content)
                discovered.extend(file_tests)
            elif any(ext in filename_lower for ext in [".cpp", ".cc", ".cxx", ".c"]):
                file_tests = TestDiscoveryEngine._discover_cpp_tests(file, raw_content)
                discovered.extend(file_tests)
            else:
                # Fallback generic discovery
                discovered.append(
                    RawTestArtifact(
                        file_path=file.path,
                        test_name=f"TestFile:{file.filename}",
                        test_framework="generic",
                        test_type=TestType.UNIT.value,
                        file_id=file.id,
                    )
                )

        return discovered

    @staticmethod
    def _is_test_file(path_lower: str, filename_lower: str, raw_content: str) -> bool:
        """Determines if a file is a test file based on path conventions or code signals."""
        if any(seg in path_lower for seg in ["/test/", "/tests/", "\\test\\", "\\tests\\", "test_", "_test", ".test.", ".spec."]):
            return True
        if any(filename_lower.startswith(prefix) for prefix in ["test_", "spec_"]):
            return True
        if any(filename_lower.endswith(suffix) for suffix in ["_test.py", "test.py", "_test.go", "test.js", "test.ts", "spec.js", "spec.ts", "test.java"]):
            return True
        if re.search(r"@Test|def test_|describe\(|it\(|TEST\(|TEST_F\(", raw_content):
            return True
        return False

    @staticmethod
    def _discover_python_tests(file: CodeFile, content: str) -> List[RawTestArtifact]:
        tests: List[RawTestArtifact] = []
        if not content:
            return tests

        lines = content.splitlines()
        framework = "pytest" if "pytest" in content else ("unittest" if "unittest" in content else "pytest")

        for i, line in enumerate(lines, start=1):
            # def test_func(...):
            m_def = re.match(r"^\s*def\s+(test_[A-Za-z0-9_]+)\s*\(", line)
            if m_def:
                test_name = m_def.group(1)
                test_type = TestType.E2E.value if "e2e" in test_name.lower() or "integration" in file.path.lower() else TestType.UNIT.value
                tests.append(
                    RawTestArtifact(
                        file_path=file.path,
                        test_name=test_name,
                        test_framework=framework,
                        test_type=test_type,
                        line_start=i,
                        file_id=file.id,
                    )
                )

            # class TestClass(unittest.TestCase):
            m_class = re.match(r"^\s*class\s+([A-Za-z0-9_]*Test[A-Za-z0-9_]*)\b", line)
            if m_class and "test" not in [t.test_name for t in tests]:
                tests.append(
                    RawTestArtifact(
                        file_path=file.path,
                        test_name=m_class.group(1),
                        test_framework=framework,
                        test_type=TestType.UNIT.value,
                        line_start=i,
                        file_id=file.id,
                    )
                )

        if not tests:
            tests.append(
                RawTestArtifact(
                    file_path=file.path,
                    test_name=f"test_{file.filename}",
                    test_framework=framework,
                    test_type=TestType.UNIT.value,
                    file_id=file.id,
                )
            )
        return tests

    @staticmethod
    def _discover_jsts_tests(file: CodeFile, content: str) -> List[RawTestArtifact]:
        tests: List[RawTestArtifact] = []
        if not content:
            return tests

        lines = content.splitlines()
        framework = "vitest" if "vitest" in content else ("jest" if "jest" in content else "mocha")

        for i, line in enumerate(lines, start=1):
            m = re.search(r"\b(it|test|describe)\s*\(\s*['\"]([^'\"]+)['\"]", line)
            if m:
                kind, name = m.group(1), m.group(2)
                test_type = TestType.E2E.value if "e2e" in name.lower() or "e2e" in file.path.lower() else TestType.UNIT.value
                tests.append(
                    RawTestArtifact(
                        file_path=file.path,
                        test_name=f"{kind}: {name}",
                        test_framework=framework,
                        test_type=test_type,
                        line_start=i,
                        file_id=file.id,
                    )
                )

        if not tests:
            tests.append(
                RawTestArtifact(
                    file_path=file.path,
                    test_name=f"test:{file.filename}",
                    test_framework=framework,
                    test_type=TestType.UNIT.value,
                    file_id=file.id,
                )
            )
        return tests

    @staticmethod
    def _discover_java_tests(file: CodeFile, content: str) -> List[RawTestArtifact]:
        tests: List[RawTestArtifact] = []
        if not content:
            return tests

        lines = content.splitlines()
        for i, line in enumerate(lines, start=1):
            if "@Test" in line:
                # Next line usually contains method def
                target_line = lines[i] if i < len(lines) else line
                m = re.search(r"\bpublic\s+void\s+([A-Za-z0-9_]+)\s*\(", target_line)
                test_name = m.group(1) if m else f"testAtLine{i}"
                tests.append(
                    RawTestArtifact(
                        file_path=file.path,
                        test_name=test_name,
                        test_framework="junit",
                        test_type=TestType.UNIT.value,
                        line_start=i,
                        file_id=file.id,
                    )
                )

        if not tests:
            tests.append(
                RawTestArtifact(
                    file_path=file.path,
                    test_name=f"JavaTest:{file.filename}",
                    test_framework="junit",
                    test_type=TestType.UNIT.value,
                    file_id=file.id,
                )
            )
        return tests

    @staticmethod
    def _discover_cpp_tests(file: CodeFile, content: str) -> List[RawTestArtifact]:
        tests: List[RawTestArtifact] = []
        if not content:
            return tests

        lines = content.splitlines()
        for i, line in enumerate(lines, start=1):
            m = re.search(r"\b(TEST|TEST_F|TEST_P)\s*\(\s*([A-Za-z0-9_]+)\s*,\s*([A-Za-z0-9_]+)\s*\)", line)
            if m:
                suite, name = m.group(2), m.group(3)
                tests.append(
                    RawTestArtifact(
                        file_path=file.path,
                        test_name=f"{suite}.{name}",
                        test_framework="gtest",
                        test_type=TestType.UNIT.value,
                        line_start=i,
                        file_id=file.id,
                    )
                )

        if not tests:
            tests.append(
                RawTestArtifact(
                    file_path=file.path,
                    test_name=f"CppTest:{file.filename}",
                    test_framework="gtest",
                    test_type=TestType.UNIT.value,
                    file_id=file.id,
                )
            )
        return tests
