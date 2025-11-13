# Dockerfile for SoulNear WebApp API v2
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy soul_bot first (for dependencies)
COPY soul_bot /app/soul_bot

# Copy and install requirements
COPY webapp_api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy webapp_api code
COPY webapp_api /app/webapp_api

# Set working directory to webapp_api
WORKDIR /app/webapp_api

# Expose port
EXPOSE 8001

# Run with hypercorn for better async support
CMD ["hypercorn", "app_v2:app", "--bind", "0.0.0.0:8001", "--workers", "2"]

