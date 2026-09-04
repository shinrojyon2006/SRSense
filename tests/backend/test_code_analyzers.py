"""
Tests for Sprint 2.0 Language AST Analyzers.

Verifies:
- Python AST analyzer (classes, functions, async methods, endpoints, db calls).
- TypeScript / JS analyzer (classes, interfaces, functions, Express routes).
- Java analyzer (packages, classes, methods, Spring routes, JPA).
- C/C++ analyzer (structs, classes, functions, includes).
- SQL analyzer (tables, views, procedures, queries).
- HTML/CSS analyzer (forms, scripts, selectors).
"""

import pytest
from app.core.code_intelligence.factory import CodeAnalyzerFactory


class TestCodeAnalyzers:

    def test_python_analyzer(self):
        py_code = '''
import os
from fastapi import APIRouter
from sqlalchemy import select

router = APIRouter()

class OrderService:
    """Handles order processing."""
    def __init__(self, db_session):
        self.db = db_session

    async def create_order(self, user_id: int, total_amount: float) -> dict:
        """Create new order in DB."""
        stmt = select(Order).where(Order.user_id == user_id)
        result = await self.db.execute(stmt)
        return {"status": "created"}

@router.post("/api/orders")
async def handle_order_post(payload: dict):
    return {"ok": True}
'''
        analyzer = CodeAnalyzerFactory.get_analyzer("Python")
        res = analyzer.analyze("app/services/order.py", "order.py", py_code, "Python", "High")

        assert res.line_count > 10
        assert len(res.imports) >= 3
        # Symbols check
        sym_names = [s.symbol_name for s in res.symbols]
        assert "OrderService" in sym_names
        assert "create_order" in sym_names
        assert "handle_order_post" in sym_names
        assert "POST /api/orders" in sym_names

        # Endpoint check
        assert len(res.endpoints) >= 1
        assert res.endpoints[0]["http_method"] == "POST"
        assert res.endpoints[0]["path"] == "/api/orders"

        # DB calls
        assert len(res.db_interactions) >= 1
        assert any("SQLAlchemy" in d["operation_type"] for d in res.db_interactions)

    def test_typescript_analyzer(self):
        ts_code = """
import React, { useState } from 'react';
import axios from 'axios';

export interface UserConfig {
    theme: string;
    notifications: boolean;
}

export class UserManager {
    async fetchUser(id: string) {
        return axios.get(`/api/users/${id}`);
    }
}

export const UserProfileCard: React.FC = () => {
    const [user, setUser] = useState(null);
    return <div>Profile</div>;
};
"""
        analyzer = CodeAnalyzerFactory.get_analyzer("TypeScript")
        res = analyzer.analyze("src/components/UserProfile.tsx", "UserProfile.tsx", ts_code, "TypeScript", "High")

        sym_names = [s.symbol_name for s in res.symbols]
        assert "UserConfig" in sym_names
        assert "UserManager" in sym_names
        assert "UserProfileCard" in sym_names
        assert len(res.imports) >= 2

    def test_java_analyzer(self):
        java_code = """
package com.srsense.service;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.data.jpa.repository.JpaRepository;

@RestController
public class AuthController {

    @GetMapping("/api/v1/auth/status")
    public String checkAuthStatus() {
        return "authenticated";
    }
}
"""
        analyzer = CodeAnalyzerFactory.get_analyzer("Java")
        res = analyzer.analyze("src/main/java/AuthController.java", "AuthController.java", java_code, "Java", "High")

        sym_names = [s.symbol_name for s in res.symbols]
        assert "AuthController" in sym_names
        assert "checkAuthStatus" in sym_names
        assert "GET /api/v1/auth/status" in sym_names
        assert len(res.endpoints) >= 1

    def test_cpp_analyzer(self):
        cpp_code = """
#include <iostream>
#include "protocol.h"

struct NetworkPacket {
    int packet_id;
    size_t payload_length;
};

class PacketProcessor : public BaseProcessor {
public:
    bool process_packet(const NetworkPacket& packet);
};
"""
        analyzer = CodeAnalyzerFactory.get_analyzer("C++")
        res = analyzer.analyze("core/processor.cpp", "processor.cpp", cpp_code, "C++", "High")

        sym_names = [s.symbol_name for s in res.symbols]
        assert "NetworkPacket" in sym_names
        assert "PacketProcessor" in sym_names
        assert len(res.imports) >= 2

    def test_sql_analyzer(self):
        sql_code = """
-- SRSense Schema
CREATE TABLE requirements (
    id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    quality_score INT
);

CREATE VIEW active_requirements AS
SELECT * FROM requirements WHERE quality_score > 70;

CREATE PROCEDURE clean_stale_data()
BEGIN
    DELETE FROM requirements WHERE quality_score < 10;
END;
"""
        analyzer = CodeAnalyzerFactory.get_analyzer("SQL")
        res = analyzer.analyze("db/schema.sql", "schema.sql", sql_code, "SQL", "High")

        sym_names = [s.symbol_name for s in res.symbols]
        assert "requirements" in sym_names
        assert "active_requirements" in sym_names
        assert "clean_stale_data" in sym_names
        assert len(res.db_interactions) >= 1

    def test_html_css_analyzers(self):
        html_code = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="styles.css">
    <script src="app.js"></script>
</head>
<body>
    <form action="/api/login" method="POST">
        <input type="text" name="username">
    </form>
</body>
</html>
"""
        html_analyzer = CodeAnalyzerFactory.get_analyzer("HTML")
        html_res = html_analyzer.analyze("public/index.html", "index.html", html_code, "HTML", "High")
        assert len(html_res.endpoints) >= 1
        assert html_res.endpoints[0]["path"] == "/api/login"

        css_code = """
@import url('fonts.css');

.primary-btn {
    background-color: #4f46e5;
}

@media (min-width: 768px) {
    .container { max-width: 720px; }
}
"""
        css_analyzer = CodeAnalyzerFactory.get_analyzer("CSS")
        css_res = css_analyzer.analyze("styles.css", "styles.css", css_code, "CSS", "High")
        sym_names = [s.symbol_name for s in css_res.symbols]
        assert ".primary-btn" in sym_names
