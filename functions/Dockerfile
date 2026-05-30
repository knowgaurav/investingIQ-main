# Azure Functions Dockerfile for InvestingIQ Durable Functions (Python)
FROM mcr.microsoft.com/azure-functions/python:4-python3.11

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

# Copy the function app
COPY . /home/site/wwwroot
