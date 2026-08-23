# ====================================================================
# Census Assistant - Production Containerization Dockerfile
# ====================================================================

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    DATA_DIR=/app/data

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend, frontend, database schemas, and data files
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY database/ ./database/
COPY *.xlsx ./
COPY *.pdf ./

# Build-time sanity check: verify the seed Excel/PDF files parse and the
# schema initializes cleanly. This writes into the image layer only — the
# entrypoint script below re-seeds the real persistent volume at runtime.
RUN mkdir -p /app/data && python -m backend.ingestion

COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["./entrypoint.sh"]
