"""
Tests for Sprint 2.0 Programming Language Detector.

Verifies:
- Accurate detection for all 9 target languages.
- Confidence levels (High, Medium, Unknown).
- Disambiguation for C vs C++ header files.
- Safe fallback for unknown/unsupported extensions.
"""

import pytest
from app.core.code_intelligence.detector import (
    LanguageDetector,
    LanguageConfidence,
)


class TestLanguageDetector:

    @pytest.mark.parametrize(
        "filename,expected_lang,expected_conf",
        [
            ("main.py", "Python", "High"),
            ("types.pyi", "Python", "High"),
            ("App.tsx", "TypeScript", "High"),
            ("service.ts", "TypeScript", "High"),
            ("index.js", "JavaScript", "High"),
            ("Component.jsx", "JavaScript", "High"),
            ("UserService.java", "Java", "High"),
            ("kernel.c", "C", "High"),
            ("engine.cpp", "C++", "High"),
            ("engine.cxx", "C++", "High"),
            ("types.hpp", "C++", "High"),
            ("index.html", "HTML", "High"),
            ("styles.css", "CSS", "High"),
            ("theme.scss", "CSS", "High"),
            ("schema.sql", "SQL", "High"),
        ],
    )
    def test_standard_extensions(self, filename, expected_lang, expected_conf):
        res = LanguageDetector.detect(filename)
        assert res.language == expected_lang
        assert res.confidence == expected_conf
        assert res.is_supported is True

    def test_header_c_vs_cpp_disambiguation(self):
        # Plain C header
        c_code = """
        #ifndef MY_HEADER_H
        #define MY_HEADER_H
        int add(int a, int b);
        #endif
        """
        c_res = LanguageDetector.detect("math_utils.h", c_code)
        assert c_res.language == "C"

        # C++ header with class & namespace
        cpp_code = """
        #pragma once
        #include <vector>
        namespace Core {
            class Engine {
            public:
                void start();
            };
        }
        """
        cpp_res = LanguageDetector.detect("engine.h", cpp_code)
        assert cpp_res.language == "C++"
        assert cpp_res.confidence == "High"

    def test_content_shebang_detection(self):
        py_script = "#!/usr/bin/env python3\nprint('hello')"
        res = LanguageDetector.detect("run_task", py_script)
        assert res.language == "Python"
        assert res.confidence == "Medium"

    def test_unknown_and_unsupported_files(self):
        unknown_files = [
            "data.xyz",
            "archive.tar.gz",
            "binary.bin",
            "model.onnx",
            "unknown_file",
        ]
        for f in unknown_files:
            res = LanguageDetector.detect(f)
            assert res.language == "Unknown / Unsupported"
            assert res.confidence == "Unknown"
            assert res.is_supported is False
