# VibeCheck Flask Application Dockerfile
# Optimized for Fly.io deployment

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.7.1

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Configure poetry to not create virtual env
RUN poetry config virtualenvs.create false

# Install Python dependencies + CLIP
RUN poetry install --only main --no-interaction --no-ansi && \
    pip install --no-cache-dir git+https://github.com/openai/CLIP.git

# Copy application code
COPY app/app.py ./app.py
COPY app/templates/ ./templates/
COPY src/ ./src/

# Copy data files
COPY data/ ./data/

# Set Python path
ENV PYTHONPATH=/app/src

# Environment variables for optimal performance
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV FLASK_ENV=production

# Expose Flask port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Run Flask application
CMD ["python", "app.py"]
