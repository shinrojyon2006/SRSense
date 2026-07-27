# SRSense AI — Local Development & Deployment Guide

This guide provides step-by-step instructions to set up, run, and deploy SRSense AI.

---

## 📋 System Prerequisites

1. **Docker & Docker Compose**: Recommended for quick setup (includes PostgreSQL database, FastAPI, Nginx).
2. **Python 3.12+**: Required for local backend development.
3. **Node.js 20+ & npm**: Required for local frontend development.
4. **PostgreSQL 16**: Required if running backend without Docker.

---

## 🚀 Option A: Run with Docker Compose (Recommended)

1. Clone or navigate to repository root:
   ```bash
   cd SRSense-AI
   ```

2. Copy environment file template:
   ```bash
   cp .env.example .env
   ```

3. Build and start containers:
   ```bash
   docker-compose up --build -d
   ```

4. Access applications:
   - **Frontend (Nginx)**: `http://localhost`
   - **Backend API**: `http://localhost:8000`
   - **Interactive API Docs**: `http://localhost:8000/docs`

5. Create First Administrator Account (Secure CLI):
   ```bash
   docker exec -it srsense-backend python create_admin.py
   ```

---

## 💻 Option B: Local Development Setup

### 1. Database Setup
Ensure PostgreSQL is running locally or via Docker:
```bash
docker run --name srsense-db -e POSTGRES_USER=srsense -e POSTGRES_PASSWORD=srsense_secret_2024 -e POSTGRES_DB=srsense_db -p 5432:5432 -d postgres:16-alpine
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv .venv
# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Create Initial Admin Account
python create_admin.py

# Start Development Server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
Open browser at `http://localhost:5173`.

---

## 🔐 Security Configuration

Edit `.env` before deploying to production:
- Set `SECRET_KEY` to a strong random string (e.g. `openssl rand -hex 32`).
- Adjust `BACKEND_CORS_ORIGINS` to allow only domain names in production.
- Configure `RATE_LIMIT_PER_MINUTE` as per server capacity.
