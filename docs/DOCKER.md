# Phase 23: Docker & Docker-Compose Guide

This guide details running the complete **AI Resume Parser & Job Matcher** application in isolated containers with Docker and Docker Compose.

---

## Architecture Overview

The multi-container Docker deployment orchestrates three networked services:

1. **`db` (PostgreSQL 16 with pgvector)**:
   - Image: `pgvector/pgvector:pg16`
   - Persistent volume: `postgres_data` mapped to `/var/lib/postgresql/data`
   - Healthcheck: `pg_isready -U postgres -d ai_resume_parser`
   - Internal Port: `5432`

2. **`backend` (FastAPI + Python 3.11)**:
   - Dockerfile: `backend/Dockerfile` (Debian-slim base with Tesseract OCR & spaCy models)
   - Depends on: `db` (`service_healthy`)
   - Auto-executes database migrations and table verification on startup
   - Healthcheck: `curl -f http://localhost:8001/api/health`
   - Internal Port: `8001`

3. **`frontend` (React 19 + Vite + Tailwind CSS v4 via Nginx)**:
   - Dockerfile: `frontend/Dockerfile` (multi-stage build with Node.js 22 builder and Nginx Alpine server)
   - Depends on: `backend` (`service_healthy`)
   - Nginx reverse-proxies `/api/` traffic directly to `http://backend:8001/api/`
   - Healthcheck: `wget -q --spider http://localhost:3000/healthz`
   - Exposed Port: `3000`

---

## Quick Reference Commands

### 1. How to Start the Entire Application

Before starting, copy the environment template to `.env` (no secrets are committed to Git):

```bash
# 1. Copy environment template
cp .env.example .env

# (Optional) Add your GEMINI_API_KEY into .env if using remote Gemini extraction:
# GEMINI_API_KEY="your-gemini-key"

# 2. Build and start all services in detached mode
docker compose up --build -d
```

Once running:
- **Web Application**: Open [http://localhost:3000](http://localhost:3000)
- **FastAPI Documentation**: Open [http://localhost:8001/docs](http://localhost:8001/docs)
- **Backend Health Check**: [http://localhost:8001/api/health](http://localhost:8001/api/health)
- **Database**: `localhost:5432` (`ai_resume_parser` database)

---

### 2. How to Stop the Application

To gracefully stop and remove containers and networks while **preserving your database volume**:

```bash
docker compose down
```

To stop containers temporarily without removing them:

```bash
docker compose stop
```

To start them back up without rebuilding:

```bash
docker compose start
```

---

### 3. How to Reset the Database

To completely wipe all persisted resumes, users, job descriptions, and vector embeddings and start completely fresh from scratch:

```bash
# 1. Stop and remove containers AND remove the persistent postgres_data volume
docker compose down -v

# 2. Start the stack again (re-provisions clean database schemas automatically)
docker compose up -d
```

Alternatively, to drop and recreate tables without restarting containers:

```bash
docker compose exec db psql -U postgres -d ai_resume_parser -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; CREATE EXTENSION IF NOT EXISTS vector;"
docker compose restart backend
```

---

### 4. How to View Logs

View live streamed logs from all services combined:

```bash
docker compose logs -f
```

View live logs from a specific service:

```bash
# Backend logs
docker compose logs -f backend

# Frontend logs
docker compose logs -f frontend

# Database logs
docker compose logs -f db
```

View the last 100 log lines with timestamps:

```bash
docker compose logs --tail=100 -t backend
```

---

## Verifying Container Health & Status

Check the operational and health status of all containers:

```bash
docker compose ps
```

Expected output:
```
NAME                      IMAGE                      STATUS                   PORTS
resume_parser_db          pgvector/pgvector:pg16     Up (healthy)             0.0.0.0:5432->5432/tcp
resume_parser_backend     applet-backend             Up (healthy)             0.0.0.0:8001->8001/tcp
resume_parser_frontend    applet-frontend            Up (healthy)             0.0.0.0:3000->3000/tcp
```

---

## Executing Commands Inside Containers

### Run Pytest Suite Inside Backend Container
```bash
docker compose exec backend python3 -m pytest backend/tests -v
```

### Run Database Migrations Manually
```bash
docker compose exec backend alembic upgrade head
```

### Connect to PostgreSQL Shell
```bash
docker compose exec db psql -U postgres -d ai_resume_parser
```

---

## Environment Variables Reference

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `POSTGRES_USER` | `postgres` | PostgreSQL superuser username |
| `POSTGRES_PASSWORD` | `postgres` | PostgreSQL superuser password |
| `POSTGRES_DB` | `ai_resume_parser` | Default relational database name |
| `POSTGRES_PORT` | `5432` | Exposed host port for PostgreSQL |
| `DATABASE_URL` | `postgresql+psycopg2://...` | Connection URI for SQLAlchemy |
| `BACKEND_PORT` | `8001` | Exposed host port for FastAPI |
| `FRONTEND_PORT` | `3000` | Exposed host port for React SPA |
| `LLM_PROVIDER` | `gemini` | Structured parser backend (`gemini` or `mock`) |
| `GEMINI_API_KEY` | *(empty)* | Optional Gemini API key for production AI |
| `EMBEDDING_PROVIDER` | `auto` | Dense embedding provider (`auto`, `gemini`, `mock`) |
| `JWT_SECRET_KEY` | *(secure default)* | 256-bit symmetric key for auth tokens |
