# Docker Quick Start Guide

Get VibeCheck running in 5 minutes!

## Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Data files downloaded from [Google Drive](https://drive.google.com/drive/folders/1EXlgII9BrqfkYYuDljkOHK8dXKCDldb6?usp=sharing)

## Setup Steps

### 1. Clone and Navigate

```bash
git clone https://github.com/your-org/VibeCheck.git
cd VibeCheck
```

### 2. Setup Data Directory

```bash
# Create data directory
mkdir -p data/images

# Copy your downloaded files to data/
# Required files:
#   - vibecheck.db
#   - vibecheck_index.faiss
#   - meta_ids.npy
#   - vibe_map.csv
#   - images/ (directory with restaurant photos)
```

### 3. Build and Run

```bash
# Build Docker image (takes ~10 minutes first time)
docker-compose build

# Start the application
docker-compose up
```

### 4. Access Application

Open browser to: **http://localhost:5000**

## Common Commands

```bash
# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop application
docker-compose down

# Rebuild after code changes
docker-compose build
docker-compose up
```

## Troubleshooting

### "Cannot find data files"
- Ensure data files are in `./data/` directory
- Check: `ls -la data/`

### "Port 5000 already in use"
Edit `docker-compose.yml`:
```yaml
ports:
  - "8080:5000"  # Use port 8080 instead
```

### "Out of memory"
- Increase Docker memory limit in Docker Desktop settings
- Minimum: 8GB, Recommended: 16GB

## Next Steps

- Read full [DOCKER_SETUP.md](DOCKER_SETUP.md) for advanced configuration
- See [DATA_SETUP.md](DATA_SETUP.md) for data file details
- Check [README.md](README.md) for project overview

## Need Help?

1. Check logs: `docker-compose logs app`
2. Verify data: `ls -lh data/`
3. Rebuild: `docker-compose build --no-cache`
4. Open GitHub issue if problem persists
