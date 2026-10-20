#!/bin/bash

# Ensure PostgreSQL service is active
service postgresql start 2>/dev/null || su - postgres -c "pg_ctlcluster 15 main start" 2>/dev/null || true

# Ensure database exists
su - postgres -c "psql -tc \"SELECT 1 FROM pg_database WHERE datname = 'ai_resume_parser'\" | grep -q 1 || psql -c 'CREATE DATABASE ai_resume_parser;'" 2>/dev/null || true

# Restart FastAPI backend on port 8001 with reload
pkill -9 -f uvicorn 2>/dev/null || true
sleep 1
echo "[Startup] Starting FastAPI backend on port 8001 with reload..."
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8001 --reload &

# Start Vite dev server on port 3000
echo "[Startup] Starting Vite dev server on port 3000..."
if [ -x "./node_modules/.bin/vite" ]; then
  exec ./node_modules/.bin/vite --port=3000 --host=0.0.0.0 "$@"
else
  exec npx vite --port=3000 --host=0.0.0.0 "$@"
fi
