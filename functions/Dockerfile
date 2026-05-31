# Azure Functions Dockerfile for InvestingIQ Durable Functions (Python)
# The base image is published for linux/amd64 only; pin the platform so it
# builds on Apple Silicon (arm64) via emulation.
FROM --platform=linux/amd64 mcr.microsoft.com/azure-functions/python:4-python3.11 AS base

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

# Install system dependencies needed by ML libs (prophet/statsmodels) and psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for better layer caching
COPY requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt

# ---------------------------------------------------------------------------
# Development stage: the Functions host reloads when files under wwwroot
# change. Source is bind-mounted in docker-compose.override.yml so edits to
# the function app are picked up live without rebuilding the image.
# ---------------------------------------------------------------------------
FROM base AS dev

COPY . /home/site/wwwroot

# ---------------------------------------------------------------------------
# Production stage (default build target).
# ---------------------------------------------------------------------------
FROM base AS prod

# Copy the function app
COPY . /home/site/wwwroot
