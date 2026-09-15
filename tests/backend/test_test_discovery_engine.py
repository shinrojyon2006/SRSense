"""
Sprint 2.4 — Test Discovery Engine Unit Tests.

Validates multi-language test file detection and test symbol extraction
across Python, JavaScript/TypeScript, Java, and C/C++.
"""

import pytest
from app.core.code_intelligence.test_discovery_engine import TestDiscoveryEngine, RawTestArtifact
from app.models.codebase import CodeFile


def test_python_pytest_discovery():
    file = CodeFile(
        id="file_1",
        path="tests/backend/test_auth.py",
        filename="test_auth.py",
        language="python",
        metadata_json={
            "raw_content": """
import pytest

def test_login_success():
    assert True

class TestUserRegistration:
    def test_register_duplicate_email(self):
        pass

    def test_register_invalid_password(self):
        pass
"""
        },
    )
    results = TestDiscoveryEngine.discover_tests([file])
    assert len(results) >= 2
    test_names = [t.test_name for t in results]
    assert "test_login_success" in test_names
    assert any("test_register_duplicate_email" in name for name in test_names)


def test_jest_javascript_discovery():
    file = CodeFile(
        id="file_2",
        path="src/components/LoginModal.test.tsx",
        filename="LoginModal.test.tsx",
        language="typescript",
        metadata_json={
            "raw_content": """
import { render, screen } from '@testing-library/react';

describe('LoginModal Component', () => {
  it('renders login form correctly', () => {
    expect(true).toBe(true);
  });

  test('submits form with valid credentials', async () => {
    expect(true).toBe(true);
  });
});
"""
        },
    )
    results = TestDiscoveryEngine.discover_tests([file])
    assert len(results) >= 1
    test_names = [t.test_name for t in results]
    assert any("renders login form correctly" in name or "renders" in name for name in test_names)


def test_java_junit_discovery():
    file = CodeFile(
        id="file_3",
        path="src/test/java/com/srsense/UserServiceTest.java",
        filename="UserServiceTest.java",
        language="java",
        metadata_json={
            "raw_content": """
package com.srsense;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class UserServiceTest {

    @Test
    public void testCreateUser() {
        assertTrue(true);
    }

    @Test
    void testDeleteUser() {
        assertNotNull(new Object());
    }
}
"""
        },
    )
    results = TestDiscoveryEngine.discover_tests([file])
    assert len(results) >= 1
    test_names = [t.test_name for t in results]
    assert any("testCreateUser" in name for name in test_names)


def test_gtest_cpp_discovery():
    file = CodeFile(
        id="file_4",
        path="tests/test_calculator.cpp",
        filename="test_calculator.cpp",
        language="cpp",
        metadata_json={
            "raw_content": """
#include <gtest/gtest.h>

TEST(CalculatorTest, HandlesAddition) {
    EXPECT_EQ(1 + 1, 2);
}

TEST_F(CalculatorFixture, HandlesDivisionByZero) {
    EXPECT_THROW(calc.divide(1, 0), std::invalid_argument);
}
"""
        },
    )
    results = TestDiscoveryEngine.discover_tests([file])
    assert len(results) >= 1
    test_names = [t.test_name for t in results]
    assert any("HandlesAddition" in name for name in test_names)


def test_non_test_file_rejected():
    file = CodeFile(
        id="file_5",
        path="app/services/user_service.py",
        filename="user_service.py",
        language="python",
        metadata_json={
            "raw_content": """
class UserService:
    def get_user(self, user_id: str):
        return {"id": user_id}
"""
        },
    )
    results = TestDiscoveryEngine.discover_tests([file])
    assert len(results) == 0
