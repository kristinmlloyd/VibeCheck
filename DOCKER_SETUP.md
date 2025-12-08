# Docker Setup Guide for VibeCheck

This guide explains how to run VibeCheck using Docker for easy deployment and consistent environments.

## Architecture Overview

The Docker setup uses a simplified single-container architecture:

```
┌─────────────────────────────────────┐
│                                     │
│    VibeCheck Flask Application     │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  Flask Web Server (Port 5000)│  │
│  ├──────────────────────────────┤  │
│  │  CLIP + Sentence-BERT Models │  │
│  ├──────────────────────────────┤  │
│  │  FAISS Vector Search         │  │
│  ├──────────────────────────────┤  │
│  │  SQLite Database             │  │
│  └──────────────────────────────┘  │
│                                     │
└─────────────────────────────────────┘
           ▲
           │
    Volume Mount: ./data (read-only)
```

**Why Single Container?**
- Flask app is self-contained with all ML models
- No need for separate API/ML service containers
- Simpler deployment and maintenance
- Faster startup time
- Lower resource usage

## Prerequisites

1. **Docker & Docker Compose** installed
   - Docker: https://docs.docker.com/get-docker/
   - Docker Compose: Usually included with Docker Desktop

2. **Data Files** downloaded and placed in `data/` directory
   - See [DATA_SETUP.md](DATA_SETUP.md) for details

3. **Minimum System Requirements**
   - 8GB RAM (16GB recommended)
   - 10GB free disk space
   - Multi-core CPU (GPU optional for faster inference)

## Quick Start

### 1. Clone Repository and Setup Data

```bash
# Clone the repository
git clone https://github.com/your-org/VibeCheck.git
cd VibeCheck

# Setup data directory (see DATA_SETUP.md)
mkdir -p data/images

# Copy your data files to data/
# - vibecheck.db
# - vibecheck_index.faiss
# - meta_ids.npy
# - vibe_map.csv
# - images/
```

### 2. Build Docker Image

```bash
docker-compose build
```

This will:
- Pull Python 3.11 base image
- Install system dependencies
- Install Python packages via Poetry
- Install CLIP model from GitHub
- Copy application code

Build time: ~10-15 minutes (first time)

### 3. Start Application

```bash
docker-compose up
```

Or run in background:
```bash
docker-compose up -d
```

### 4. Access Application

Open your browser to:
- **Application**: http://localhost:5000

### 5. Check Logs

```bash
# View logs
docker-compose logs -f app

# View logs for last 100 lines
docker-compose logs --tail=100 app
```

### 6. Stop Application

```bash
# Stop containers
docker-compose down

# Stop and remove volumes (cleanup)
docker-compose down -v
```

## Configuration

### Environment Variables

Edit `docker-compose.yml` to customize:

```yaml
environment:
  - FLASK_ENV=production           # Flask environment
  - OUTPUT_DIR=/app/data           # Data directory path
  - DB_PATH=/app/data/vibecheck.db # Database path
  - OMP_NUM_THREADS=1              # OpenMP threads
  - MKL_NUM_THREADS=1              # MKL threads
```

### Port Mapping

Change exposed port in `docker-compose.yml`:

```yaml
ports:
  - "8080:5000"  # Map container port 5000 to host port 8080
```

### Volume Mounts

The data directory is mounted as read-only for safety:

```yaml
volumes:
  - ./data:/app/data:ro  # :ro = read-only
```

To allow writes (not recommended):
```yaml
volumes:
  - ./data:/app/data:rw  # :rw = read-write
```

## Development Workflow

### Local Development (without Docker)

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install poetry
poetry install

# Run Flask app
python scripts/app.py
```

### Development with Docker

Mount code as volume for live reloading:

```yaml
# Add to docker-compose.yml under app service
volumes:
  - ./data:/app/data:ro
  - ./scripts/app.py:/app/app.py  # Live reload Flask app
  - ./scripts/templates:/app/templates  # Live reload templates
```

Then:
```bash
docker-compose up
# Edit code locally, Flask auto-reloads inside container
```

## Troubleshooting

### Container Fails to Start

**Check logs:**
```bash
docker-compose logs app
```

**Common issues:**
1. Missing data files → See DATA_SETUP.md
2. Port already in use → Change port mapping
3. Out of memory → Increase Docker memory limit

### Models Not Loading

**Symptoms:** Error loading CLIP or Sentence-BERT models

**Solutions:**
```bash
# Clear model cache and rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### Database Connection Errors

**Check database file exists:**
```bash
ls -lh data/vibecheck.db
```

**Check file permissions:**
```bash
chmod 644 data/vibecheck.db
```

### Slow Search Performance

**Use GPU acceleration (if available):**

1. Install NVIDIA Container Toolkit
2. Update `docker-compose.yml`:
```yaml
app:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

### Cannot Access Application

**Check container status:**
```bash
docker-compose ps
```

**Check health:**
```bash
docker-compose exec app curl http://localhost:5000/
```

**Check firewall:**
```bash
# Allow port 5000
sudo ufw allow 5000
```

## Production Deployment

### Using Nginx Reverse Proxy

Uncomment nginx service in `docker-compose.yml`:

```yaml
nginx:
  image: nginx:alpine
  container_name: vibecheck-nginx
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - ./docker/nginx/ssl:/etc/nginx/ssl:ro
  depends_on:
    - app
```

Create `docker/nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream flask_app {
        server app:5000;
    }

    server {
        listen 80;
        server_name your-domain.com;

        location / {
            proxy_pass http://flask_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Increase timeout for long-running searches
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

### SSL/TLS Configuration

1. Get SSL certificates (Let's Encrypt):
```bash
certbot certonly --standalone -d your-domain.com
```

2. Copy certificates:
```bash
mkdir -p docker/nginx/ssl
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem docker/nginx/ssl/
cp /etc/letsencrypt/live/your-domain.com/privkey.pem docker/nginx/ssl/
```

3. Update nginx.conf for HTTPS

### Resource Limits

Prevent container from using all system resources:

```yaml
app:
  deploy:
    resources:
      limits:
        cpus: '4.0'
        memory: 8G
      reservations:
        cpus: '2.0'
        memory: 4G
```

### Health Monitoring

Use Docker health checks:

```bash
# Check container health
docker-compose ps

# Get health status
docker inspect --format='{{json .State.Health}}' vibecheck-app
```

### Logging

Configure logging driver:

```yaml
app:
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
```

### Auto-restart on Failure

Already configured with:
```yaml
restart: unless-stopped
```

Options:
- `no`: Never restart
- `always`: Always restart
- `on-failure`: Restart only if container exits with error
- `unless-stopped`: Always restart unless explicitly stopped

## Docker Commands Reference

```bash
# Build/Rebuild
docker-compose build                    # Build images
docker-compose build --no-cache        # Build from scratch

# Start/Stop
docker-compose up                       # Start in foreground
docker-compose up -d                    # Start in background
docker-compose down                     # Stop and remove containers
docker-compose restart                  # Restart services

# Logs
docker-compose logs                     # View all logs
docker-compose logs -f app             # Follow app logs
docker-compose logs --tail=50 app      # Last 50 lines

# Container Management
docker-compose ps                       # List running containers
docker-compose exec app bash           # Shell into container
docker-compose top                      # Display running processes

# Cleanup
docker-compose down -v                  # Remove containers and volumes
docker system prune -a                 # Remove unused images/containers
```

## Updating Application

### Update Code Only

```bash
git pull origin main
docker-compose restart
```

### Update Dependencies

```bash
git pull origin main
docker-compose build
docker-compose up -d
```

### Update Data Files

```bash
# Stop application
docker-compose down

# Update data files in data/ directory
cp new_vibecheck.db data/
cp new_vibecheck_index.faiss data/

# Restart
docker-compose up -d
```

## Multi-Container Architecture (Optional)

If you need to scale or separate concerns, you can split into multiple containers:

```yaml
services:
  frontend:
    build: ./docker/frontend
    ports:
      - "5000:5000"
    depends_on:
      - api

  api:
    build: ./docker/api
    ports:
      - "8000:8000"
    depends_on:
      - ml-service

  ml-service:
    build: ./docker/ml-service
    ports:
      - "8002:8002"
```

See the old `docker/frontend`, `docker/api`, and `docker/ml-service` Dockerfiles as reference.

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Flask in Docker](https://flask.palletsprojects.com/en/3.0.x/deploying/docker/)
- [DATA_SETUP.md](DATA_SETUP.md) - Data file setup guide
- [README.md](README.md) - Project overview and features

## Support

For issues or questions:
1. Check troubleshooting section above
2. View logs: `docker-compose logs`
3. Open an issue on GitHub
4. Contact maintainers
