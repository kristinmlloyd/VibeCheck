# Docker Configuration Files

This directory contains Docker configuration files for the VibeCheck application.

## Current Architecture (Flask Monolith)

```
docker/
├── app/
│   └── Dockerfile          # Active: Flask application container
├── frontend/               # Legacy: Old Streamlit frontend
├── api/                    # Legacy: Old FastAPI backend
└── ml-service/             # Legacy: Old ML inference service
```

## Active Configuration

### `app/Dockerfile`

**Purpose:** Flask application with integrated ML models

**Contains:**
- Python 3.11 slim base
- Poetry dependency management
- Flask web server
- CLIP + Sentence-BERT models
- FAISS vector search
- SQLite database access

**Build:**
```bash
docker build -f docker/app/Dockerfile -t vibecheck:latest .
```

**Run:**
```bash
docker run -p 5000:5000 -v $(pwd)/data:/app/data:ro vibecheck:latest
```

## Legacy Files

The `frontend/`, `api/`, and `ml-service/` directories contain the old microservices architecture that has been replaced by the consolidated Flask app.

**Why they're kept:**
- Reference for potential future scaling
- Backup if rollback is needed
- Documentation of architecture evolution

**Can be removed if:**
- New architecture is stable in production
- No plans to revert
- Team agrees to cleanup

To remove:
```bash
rm -rf docker/frontend docker/api docker/ml-service
```

## Using Docker Compose

**Recommended:** Use docker-compose from project root instead of building individual images:

```bash
# From project root
docker-compose build
docker-compose up
```

This handles:
- Building the image
- Setting environment variables
- Mounting volumes
- Network configuration
- Health checks

## Configuration Notes

### Environment Variables

Set in `docker-compose.yml`:
```yaml
environment:
  - OUTPUT_DIR=/app/data
  - DB_PATH=/app/data/vibecheck.db
  - IMAGE_DIR=/app/data/images
  - FAISS_PATH=/app/data/vibecheck_index.faiss
  - META_PATH=/app/data/meta_ids.npy
  - VIBE_MAP_CSV=/app/data/vibe_map.csv
```

### Volume Mounts

Data directory mounted read-only:
```yaml
volumes:
  - ./data:/app/data:ro
```

Model cache persisted:
```yaml
volumes:
  - model-cache:/root/.cache
```

### Ports

Flask runs on port 5000:
```yaml
ports:
  - "5000:5000"
```

## Advanced Usage

### Multi-Stage Builds

For smaller production images, consider multi-stage build:

```dockerfile
# Builder stage
FROM python:3.11-slim as builder
WORKDIR /app
RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt -o requirements.txt

# Runtime stage
FROM python:3.11-slim
COPY --from=builder /app/requirements.txt .
RUN pip install -r requirements.txt
COPY scripts/app.py .
CMD ["python", "app.py"]
```

### GPU Support

For GPU-accelerated inference:

```dockerfile
FROM nvidia/cuda:12.0-runtime-ubuntu22.04
# ... rest of Dockerfile
```

And in docker-compose:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

### Development Mode

For live code reloading:

```yaml
# Add to docker-compose.yml
volumes:
  - ./scripts/app.py:/app/app.py
  - ./scripts/templates:/app/templates
environment:
  - FLASK_DEBUG=1
```

## Documentation

- [DOCKER_QUICKSTART.md](../DOCKER_QUICKSTART.md) - Quick start guide
- [DOCKER_SETUP.md](../DOCKER_SETUP.md) - Complete setup guide
- [DATA_SETUP.md](../DATA_SETUP.md) - Data configuration
- [DOCKER_MIGRATION_SUMMARY.md](../DOCKER_MIGRATION_SUMMARY.md) - Architecture changes

## Questions?

See project root documentation or open an issue on GitHub.
