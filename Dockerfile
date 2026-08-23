# ====================================================================
# Census Assistant - Production Containerization Dockerfile
# ====================================================================

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

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

# Run initial ingestion and verify SQLite database creation
RUN python -m backend.ingestion

EXPOSE 8080

CMD ["python", "-m", "backend.main"]
