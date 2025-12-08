# VibeCheck Flask Application Dockerfile
# Optimized for production deployment with all models and dependencies

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry for dependency management
RUN pip install --no-cache-dir poetry==1.7.1

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Configure poetry to not create virtual env (we're in container)
RUN poetry config virtualenvs.create false

# Install Python dependencies
# Install main dependencies + CLIP from git
RUN poetry install --only main --no-interaction --no-ansi && \
    pip install --no-cache-dir git+https://github.com/openai/CLIP.git

# Copy application code
COPY app/app.py ./app.py
COPY app/templates/ ./templates/
COPY src/ ./src/

# Set Python path
ENV PYTHONPATH=/app/src

# Environment variables for optimal performance
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV FLASK_ENV=production

# Default paths (can be overridden in docker-compose)
ENV OUTPUT_DIR=/app/data
ENV DB_PATH=/app/data/vibecheck.db
ENV IMAGE_DIR=/app/data/images
ENV FAISS_PATH=/app/data/vibecheck_index.faiss
ENV META_PATH=/app/data/meta_ids.npy
ENV VIBE_MAP_CSV=/app/data/vibe_map.csv

# Expose Flask port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Run Flask application
CMD ["python", "app.py"]
