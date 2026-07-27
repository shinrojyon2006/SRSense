# SRSense AI — Software Requirements Engineering Platform

![SRSense AI Banner](https://img.shields.io/badge/SRSense_AI-Sprint_1.1_Foundation-4F46E5?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react)
![TailwindCSS v4](https://img.shields.io/badge/TailwindCSS-v4-38BDF8?style=for-the-badge&logo=tailwindcss)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-4169E1?style=for-the-badge&logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Multi--stage-2496ED?style=for-the-badge&logo=docker)

**SRSense AI** is a production-grade AI-powered Software Requirements Engineering Platform. This repository contains **Sprint 1.1 (Project Foundation)**, built following Clean Architecture, SOLID principles, and enterprise software standards.

---

## Architecture & Tech Stack

### Frontend
- **Framework**: React 18 with Vite
- **Styling**: Tailwind CSS v4 (`@tailwindcss/vite`)
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **Animations**: Framer Motion
- **Icons**: Lucide React
- **Design Inspiration**: Linear, GitHub, Notion, Vercel

### Backend
- **Framework**: FastAPI (Python 3.12)
- **Database Engine**: Async SQLAlchemy 2.0 with `asyncpg`
- **Database**: PostgreSQL 18
- **Database Migrations**: Alembic
- **Configuration**: Pydantic Settings
- **Logging**: Structured console logging

### Infrastructure
- **Containerization**: Multi-stage Docker builds
- **Orchestration**: Docker Compose
- **Web Server**: Nginx Alpine

---

## Project Folder Structure

```text
SRSense-AI/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   └── health.py    # Health check endpoint controller
│   │   │   └── router.py        # Central API router
│   │   ├── core/
│   │   │   ├── config.py        # Pydantic Settings
│   │   │   ├── exceptions.py    # Global Exception Handlers
│   │   │   └── logging.py       # Structured Logger
│   │   ├── db/
│   │   │   ├── base.py          # Declarative Base & Connection Verification
│   │   │   └── session.py       # Async SQLAlchemy Session & Engine
│   │   └── main.py              # FastAPI Application Factory
│   ├── alembic/                 # Alembic Database Migrations Setup
│   ├── alembic.ini
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/          # Header, Footer, Layout
│   │   │   └── ui/              # Button, Card, ThemeToggle
│   │   ├── pages/               # LandingPage, NotFoundPage
│   │   ├── services/            # Axios API client & Health check
│   │   ├── App.jsx              # React Router Routing
│   │   ├── index.css            # Tailwind CSS v4 Stylesheet
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── docker/
│   ├── backend.Dockerfile       # Multi-stage Python 3.12 Dockerfile
│   ├── frontend.Dockerfile      # Multi-stage Node 20 -> Nginx Alpine Dockerfile
│   └── nginx.conf               # Nginx SPA & API Proxy Configuration
├── docs/
│   └── ARCHITECTURE.md          # Technical Architecture Documentation
├── scripts/
│   └── setup.sh                 # Environment Setup Script
├── tests/
│   └── test_health.py           # Pytest Health Check Endpoint Suite
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI Workflow
├── .env.example                 # Environment Variables Template
├── .gitignore
├── docker-compose.yml           # Docker Compose Orchestration
└── README.md
```

---

## Quick Start & Development

### 1. Run with Docker Compose (Recommended)

```bash
# Clone or navigate to the workspace
cd SRSense-AI

# Create environment configuration file
cp .env.example .env

# Build and start services using Docker Compose
docker-compose up --build -d
```

**Access Endpoints**:
- **Frontend SPA**: `http://localhost`
- **Backend Health Check**: `http://localhost:8000/api/health`
- **Swagger API Docs**: `http://localhost:8000/docs`

---

### 2. Local Manual Development Setup

#### Backend (Python 3.12)
```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
uvicorn app.main:app --reload --port 8000
```

#### Frontend (React + Vite + Tailwind CSS v4)
```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```

#### Run Health Check Tests
```bash
pytest tests/
```
