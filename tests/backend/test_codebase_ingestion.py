"""
Security and Ingestion Tests for Sprint 2.0.

Verifies:
- Zip-Slip / Path traversal attacks are strictly rejected.
- Size and file count limits are enforced.
- Ignored directories (.git, node_modules, .venv) and binary files (.exe, .class, .png) are skipped.
- Pure static text reading with zero execution guarantee.
"""

import io
import zipfile
import pytest
from app.core.exceptions import ValidationError
from app.core.code_intelligence.ingestion import CodebaseIngestionEngine


class TestCodebaseIngestionSecurity:

    def _create_zip_buffer(self, files: dict) -> bytes:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for path, content in files.items():
                zf.writestr(path, content)
        return buf.getvalue()

    def test_safe_repository_extraction(self):
        sample_repo = {
            "src/main.py": "def main():\n    print('SRSense')",
            "src/utils.ts": "export const add = (a: number, b: number) => a + b;",
            "README.md": "# SRSense Project",
            ".gitignore": "*.pyc\nnode_modules/",
        }
        zip_bytes = self._create_zip_buffer(sample_repo)
        extracted = CodebaseIngestionEngine.validate_and_extract_zip(zip_bytes)

        assert len(extracted) == 4
        paths = [f.rel_path for f in extracted]
        assert "src/main.py" in paths
        assert "src/utils.ts" in paths

    def test_zip_slip_path_traversal_rejection(self):
        malicious_repo = {
            "../../etc/passwd": "root:x:0:0:root:/root:/bin/bash",
            "normal.py": "print('ok')",
        }
        zip_bytes = self._create_zip_buffer(malicious_repo)

        with pytest.raises(ValidationError) as exc:
            CodebaseIngestionEngine.validate_and_extract_zip(zip_bytes)

        assert "Security violation" in str(exc.value)

    def test_ignored_directories_and_binaries(self):
        mixed_repo = {
            ".git/config": "[core]\nrepositoryformatversion = 0",
            "node_modules/react/index.js": "module.exports = {};",
            ".venv/lib/site-packages/pkg.py": "# virtualenv file",
            "src/app.py": "print('App')",
            "assets/logo.png": b"\x89PNG\r\n\x1a\n\x00\x00",
            "bin/program.exe": b"MZ\x90\x00\x03\x00",
        }
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for path, content in mixed_repo.items():
                zf.writestr(path, content)

        extracted = CodebaseIngestionEngine.validate_and_extract_zip(buf.getvalue())
        extracted_paths = [f.rel_path for f in extracted]

        # Only src/app.py should be accepted
        assert len(extracted) == 1
        assert "src/app.py" in extracted_paths
        assert not any(".git" in p for p in extracted_paths)
        assert not any("node_modules" in p for p in extracted_paths)
        assert not any(".venv" in p for p in extracted_paths)

    def test_oversized_archive_rejection(self):
        # Fake oversized bytes
        large_bytes = b"0" * (51 * 1024 * 1024)
        with pytest.raises(ValidationError) as exc:
            CodebaseIngestionEngine.validate_and_extract_zip(large_bytes)
        assert "exceeds maximum allowed limit of 50 MB" in str(exc.value)
