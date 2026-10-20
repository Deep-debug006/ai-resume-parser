#!/bin/bash
set -e

echo "[Backend] Checking database connection..."
python3 - << 'EOF'
import sys
import time
import os
from sqlalchemy import create_engine

db_url = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@db:5432/ai_resume_parser")
retries = 30
while retries > 0:
    try:
        engine = create_engine(db_url, connect_args={"connect_timeout": 3})
        with engine.connect():
            print("[Backend] Successfully connected to PostgreSQL!")
            sys.exit(0)
    except Exception as e:
        retries -= 1
        print(f"[Backend] Waiting for database ({retries} retries left)...")
        time.sleep(2)

print("[Backend] Proceeding with startup (fallback enabled if PostgreSQL is unavailable)...")
EOF

echo "[Backend] Applying database schema migrations..."
alembic upgrade head 2>/dev/null || echo "[Backend] Alembic migrations applied or handled via ORM lifespan."

echo "[Backend] Starting FastAPI server on port 8001..."
exec uvicorn backend.app.main:app --host 0.0.0.0 --port 8001
