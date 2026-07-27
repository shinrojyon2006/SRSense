# SRSense AI — Technical Architecture (Sprint 1.1)

## Overview

SRSense AI is an AI-powered Software Requirements Engineering Platform. Sprint 1.1 lays the foundational architecture built using Clean Architecture principles, ensuring modularity, testability, and future scalability.

---

## Technical Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend UI** | React 18, Vite | Single Page Application framework & HMR build tool |
| **Styling** | Tailwind CSS v4 | Utility-first styling with `@tailwindcss/vite` |
| **Animations** | Framer Motion | Smooth micro-animations |
| **Icons** | Lucide React | Icon set |
| **HTTP Client** | Axios | Backend REST API communication |
| **Routing** | React Router v6 | Client-side routing |
| **Backend Framework** | FastAPI (Python 3.12) | Asynchronous REST API engine |
| **ORM & Database** | Async SQLAlchemy 2.0, PostgreSQL 18 | Data persistence with connection pooling |
| **Migrations** | Alembic | Database schema migrations pipeline |
| **Config & Validation**| Pydantic v2 Settings | Typed environment variable loading |
| **Containerization** | Docker & Docker Compose | Multi-stage production container builds |

---

## Clean Architecture Layers

```text
       ┌────────────────────────────────────────┐
       │             API Routes Layer           │
       │       (app/api/routes/health.py)       │
       └───────────────────┬────────────────────┘
                           │
       ┌───────────────────▼────────────────────┐
       │             Core Config & DB           │
       │      (app/core/config.py, app/db/)     │
       └───────────────────┬────────────────────┘
                           │
       ┌───────────────────▼────────────────────┐
       │            Database Layer              │
       │        (PostgreSQL 18 Async Engine)    │
       └────────────────────────────────────────┘
```

---

## Health Endpoint Specification

`GET /api/health`

**Response (200 OK)**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected"
}
```
