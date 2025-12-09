# VibeCheck Flask Application - Optimized for Render
# This is a simplified Dockerfile for Render deployment

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY src/ ./src/

# Set Python path
ENV PYTHONPATH=/app/src

# Environment variables for optimal performance
ENV FLASK_ENV=production
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1

# Expose port (Render will set PORT env var)
EXPOSE 8080

# Health check - give extra time for model loading
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Run with Gunicorn for production
# 2 workers, 2 threads each, 120s timeout for ML inference
CMD gunicorn --chdir app --bind 0.0.0.0:8080 --workers 2 --threads 2 --timeout 120 app:app
