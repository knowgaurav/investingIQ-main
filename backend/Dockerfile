# Backend Dockerfile for InvestingIQ FastAPI
FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Development stage: hot reload via uvicorn --reload.
# Source is bind-mounted in docker-compose.override.yml so edits reload live.
# Runs as root to avoid permission clashes with the mounted volume.
# ---------------------------------------------------------------------------
FROM base AS dev

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---------------------------------------------------------------------------
# Production stage (default build target).
# ---------------------------------------------------------------------------
FROM base AS prod

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
