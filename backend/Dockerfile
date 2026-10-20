# Multi-stage / Production-ready Python 3.11 image for FastAPI backend
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system packages required for OCR, PostgreSQL drivers, and container health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements and spaCy language model
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt && \
    pip install --no-cache-dir https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl

# Copy database migration configs and application source code
COPY alembic.ini /app/alembic.ini
COPY backend /app/backend

# Ensure entrypoint script is executable
RUN chmod +x /app/backend/entrypoint.sh

# Expose backend API port
EXPOSE 8001

# Docker container health check verifying /api/health endpoint
HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8001/api/health || exit 1

ENTRYPOINT ["/app/backend/entrypoint.sh"]
