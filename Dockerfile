# MultiMind AI Production Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (build-essential, libmagic, curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and static assets
COPY app/ ./app/
COPY static/ ./static/
COPY docs/ ./docs/

# Create data directories
RUN mkdir -p data/uploads data/processed data/vector_store

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run Uvicorn application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
