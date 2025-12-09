# Render Deployment Guide for VibeCheck

This guide walks you through deploying your Dockerized VibeCheck Flask app on Render.

## Prerequisites

1. A Render account (sign up at https://render.com)
2. Git repository pushed to GitHub/GitLab/Bitbucket
3. Your data files ready to upload (or accessible via external storage)
4. Docker image built and tested locally

## Why Render?

- **Native Docker Support**: Render natively supports Docker deployments
- **Persistent Disks**: Built-in persistent storage for your data files
- **Competitive Pricing**: More affordable than some alternatives
- **Automatic Deploys**: CI/CD built-in with GitHub integration

## Quick Start: Deployment Steps

### 1. Prepare Your Dockerfile

Your project already has a Dockerfile at [docker/app/Dockerfile](docker/app/Dockerfile). However, Render expects the Dockerfile at the **root** of your repository.

**Option A: Copy Dockerfile to root** (Recommended)
```bash
cp docker/app/Dockerfile ./Dockerfile
```

**Option B: Use render.yaml** (see Configuration section below)

### 2. Create `render.yaml` (Optional but Recommended)

Create a `render.yaml` file in your project root for infrastructure-as-code:

```yaml
services:
  - type: web
    name: vibecheck-app
    runtime: docker
    dockerfilePath: ./Dockerfile
    dockerContext: .
    plan: standard  # Minimum: standard (2GB RAM) for ML models
    envVars:
      - key: FLASK_ENV
        value: production
      - key: FLASK_PORT
        value: 8080
      - key: PORT
        value: 8080
      - key: PYTHONUNBUFFERED
        value: 1
      - key: OUTPUT_DIR
        value: /app/data
      - key: DB_PATH
        value: /app/data/vibecheck.db
      - key: IMAGE_DIR
        value: /app/data/images
      - key: FAISS_PATH
        value: /app/data/vibecheck_index.faiss
      - key: META_PATH
        value: /app/data/meta_ids.npy
      - key: VIBE_MAP_CSV
        value: /app/data/vibe_map.csv
    disk:
      name: vibecheck-data
      mountPath: /app/data
      sizeGB: 10  # Adjust based on your data size
```

### 3. Modify Dockerfile for Render (Important!)

Render requires your app to listen on the `PORT` environment variable. Update your Dockerfile:

**Original:**
```dockerfile
CMD ["python", "app.py"]
```

**For Render (recommended):**
```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "2", "--timeout", "120", "app:app"]
```

Or modify [app/app.py](app/app.py:411) to use `$PORT`:
```python
port = int(os.getenv("PORT", 8080))
```

### 4. Push Your Code to Git

```bash
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

### 5. Deploy on Render

#### Method A: Using Render Dashboard (Easiest)

1. **Go to https://render.com** and log in
2. **Click "New +"** → **"Web Service"**
3. **Connect your GitHub repository**
4. **Configure the service:**
   - **Name**: `vibecheck-app`
   - **Runtime**: Docker
   - **Region**: Choose closest to your users
   - **Branch**: `main` (or your default branch)
   - **Instance Type**: **Standard** (2GB RAM minimum)
     - ⚠️ **Important**: Starter (512MB) is **NOT sufficient** for ML models

5. **Add Environment Variables** (if not using render.yaml):
   ```
   PORT=8080
   FLASK_ENV=production
   PYTHONUNBUFFERED=1
   OUTPUT_DIR=/app/data
   DB_PATH=/app/data/vibecheck.db
   IMAGE_DIR=/app/data/images
   FAISS_PATH=/app/data/vibecheck_index.faiss
   META_PATH=/app/data/meta_ids.npy
   VIBE_MAP_CSV=/app/data/vibe_map.csv
   ```

6. **Add Persistent Disk**:
   - Click **"Add Disk"**
   - **Name**: `vibecheck-data`
   - **Mount Path**: `/app/data`
   - **Size**: 10GB (adjust based on your data)

7. **Click "Create Web Service"**

#### Method B: Using render.yaml (Infrastructure as Code)

1. If you created `render.yaml`, Render will detect it automatically
2. Go to https://dashboard.render.com/select-repo
3. Choose your repository
4. Render will read the YAML and configure everything automatically
5. Click **"Apply"**

### 6. Upload Data Files

After your service is created, you need to upload your data files to the persistent disk.

#### Option A: Using Render Shell (Recommended for small files)

1. Go to your service in Render dashboard
2. Click **"Shell"** tab
3. Upload files manually or use:
   ```bash
   cd /app/data
   # Use file upload feature in shell interface
   ```

#### Option B: Using External Storage (Recommended for large files)

For large datasets (>1GB), consider using cloud storage:

**Using AWS S3, Google Cloud Storage, or similar:**

1. Upload your data files to cloud storage
2. Add download script to your Dockerfile:
   ```dockerfile
   # Add before CMD instruction
   RUN apt-get update && apt-get install -y awscli
   ```

3. Add init script to download data on startup:
   ```dockerfile
   COPY scripts/download-data.sh /app/
   CMD ["/bin/bash", "-c", "bash /app/download-data.sh && gunicorn --bind 0.0.0.0:8080 --workers 2 --threads 2 --timeout 120 app:app"]
   ```

#### Option C: Build Data into Docker Image (Not Recommended)

Only for smaller datasets (<500MB):

1. Add data to your repository
2. Update Dockerfile:
   ```dockerfile
   COPY data/ /app/data/
   ```
3. ⚠️ **Warning**: This will make your Docker image very large and slow to build/deploy

### 7. Access Your App

Once deployed:
- Your app will be available at: `https://vibecheck-app-xxxx.onrender.com`
- Find your URL in **Dashboard** → **Your Service** → **URL** at the top
- Optionally add a **custom domain** in Settings

## Important Configuration Details

### Memory Requirements

Your app loads heavy ML models (CLIP, Sentence Transformers, FAISS):
- **Minimum RAM**: 2GB (Standard plan)
- **Recommended RAM**: 4GB (Standard Plus)
- **Startup time**: 2-3 minutes for model loading

### Render Instance Types & Pricing

| Plan | RAM | vCPU | Price | Suitable? |
|------|-----|------|-------|-----------|
| Starter | 512MB | 0.5 | $7/mo | ❌ Too small |
| Standard | 2GB | 1 | $25/mo | ✅ Minimum |
| Standard Plus | 4GB | 2 | $85/mo | ✅ Recommended |
| Pro | 8GB | 2 | $175/mo | ✅ Best performance |

### Dockerfile Optimization

Your existing [docker/app/Dockerfile](docker/app/Dockerfile:60) uses Poetry. Consider simplifying for Render:

**Simplified Dockerfile for Render:**
```dockerfile
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

# Environment variables
ENV FLASK_ENV=production
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Run with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "2", "--timeout", "120", "app.app:app"]
```

Note the last line: `app.app:app` refers to `app/app.py:app` (Flask instance).

## Troubleshooting

### App Crashes on Startup

**Symptom**: Service fails to start, shows "out of memory" errors

**Solution**:
- Upgrade to Standard plan (2GB) or higher
- Check logs: Dashboard → Your Service → Logs
- Reduce workers in CMD: `--workers 1 --threads 1`

### Models Fail to Load

**Symptom**: Errors about missing models or CUDA

**Solution**:
- Ensure `faiss-cpu` is in requirements (not `faiss-gpu`)
- Check PyTorch installation: `torch>=2.9.1` with CPU support
- Verify in [requirements.txt](requirements.txt:11-12)

### Data Files Not Found

**Symptom**: `FileNotFoundError` for database or index files

**Solution**:
- Verify persistent disk is mounted at `/app/data`
- Check environment variables match actual file locations
- Use Shell to verify files exist: `ls -lah /app/data`

### Slow First Request (Cold Start)

**Symptom**: First request takes 30+ seconds

**Solution**:
- Models load on startup (should see in logs)
- If loading on first request, add warmup in [app/app.py](app/app.py:50-55)
- Consider keeping instance always on (paid plans only)

### Images Not Displaying

**Symptom**: Search results show but images are broken

**Solution**:
- Verify `IMAGE_DIR` path: `/app/data/images`
- Check image serving route at [app/app.py:397-401](app/app.py#L397-L401)
- Ensure images uploaded to persistent disk

### Build Timeout

**Symptom**: Docker build times out

**Solution**:
- Render has 15-minute build timeout
- Cache Docker layers by ordering COPY commands properly
- Consider pre-building image and pushing to Docker Hub

## Advanced: Using Pre-Built Docker Images

For faster deploys, push to Docker Hub and use in Render:

1. **Build and push locally:**
   ```bash
   docker build -t yourusername/vibecheck:latest -f docker/app/Dockerfile .
   docker push yourusername/vibecheck:latest
   ```

2. **Update render.yaml:**
   ```yaml
   services:
     - type: web
       name: vibecheck-app
       runtime: image
       image:
         url: docker.io/yourusername/vibecheck:latest
   ```

3. **Deploy**: Render pulls pre-built image (much faster)

## Monitoring & Logs

- **Logs**: Dashboard → Your Service → Logs (real-time)
- **Metrics**: Dashboard → Your Service → Metrics (CPU, Memory, etc.)
- **Health Checks**: Configured in Dockerfile, visible in dashboard
- **Alerts**: Set up email alerts for service failures

## Cost Estimation

**Monthly cost breakdown:**
- **Web Service** (Standard, 2GB): $25/month
- **Persistent Disk** (10GB): $1/month
- **Bandwidth**: First 100GB free, then $0.10/GB
- **Total**: ~$26-30/month

**For better performance (Standard Plus, 4GB):**
- **Web Service**: $85/month
- **Total**: ~$86-90/month

## Comparison: Render vs Railway

| Feature | Render | Railway |
|---------|--------|---------|
| Docker Support | Native | Native |
| Free Tier RAM | 512MB | 512MB |
| Paid Tier Start | $25 (2GB) | $20 (Pro plan) |
| Persistent Storage | Built-in Disks | Volumes |
| Build Time | 15 min timeout | 30 min timeout |
| Custom Domains | Free SSL | Free SSL |
| Deployment Speed | Medium | Fast |

## Next Steps Checklist

- [ ] Copy Dockerfile to project root or create render.yaml
- [ ] Push code to GitHub
- [ ] Create Render account
- [ ] Deploy web service with Standard plan (2GB)
- [ ] Add persistent disk (10GB)
- [ ] Configure environment variables
- [ ] Upload data files to persistent disk
- [ ] Test your deployment
- [ ] Set up custom domain (optional)
- [ ] Configure monitoring alerts

## Support Resources

- **Render Docs**: https://render.com/docs
- **Render Community**: https://community.render.com
- **Docker on Render**: https://render.com/docs/docker
- **Persistent Disks**: https://render.com/docs/disks

---

**Ready to deploy?** Start with the Quick Start section above!
