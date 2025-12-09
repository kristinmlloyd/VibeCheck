# Railway Deployment Guide for VibeCheck

This guide walks you through deploying your VibeCheck Flask app on Railway.

## Prerequisites

1. A Railway account (sign up at https://railway.app)
2. Git repository pushed to GitHub/GitLab/Bitbucket
3. Your data files ready to upload

## Files Created for Railway

The following files have been created to support Railway deployment:

- `requirements.txt` - Python dependencies
- `Procfile` - Process configuration for Railway
- `railway.toml` - Railway-specific configuration

## Deployment Steps

### 1. Push Your Code to Git

Make sure all your changes are committed and pushed:

```bash
git add .
git commit -m "Add Railway deployment configuration"
git push origin main
```

### 2. Create a New Railway Project

1. Go to https://railway.app and log in
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your VibeCheck repository
5. Railway will automatically detect your Python app

### 3. Configure Environment Variables

In your Railway project dashboard, go to **Variables** and add these:

**Required Variables:**
```
PORT=8080
FLASK_ENV=production
PYTHONUNBUFFERED=1
```

**Optional (if paths differ from defaults):**
```
OUTPUT_DIR=/app/data
DB_PATH=/app/data/vibecheck.db
IMAGE_DIR=/app/data/images
FAISS_PATH=/app/data/vibecheck_index.faiss
META_PATH=/app/data/meta_ids.npy
VIBE_MAP_CSV=/app/data/vibe_map.csv
```

### 4. Upload Data Files

Your app needs these data files to run. You have two options:

#### Option A: Add to Repository with Git LFS (Recommended for < 2GB)

If your data files are not too large:

```bash
# Initialize Git LFS if not already done
git lfs install

# Track your data files
git lfs track "data/**/*.db"
git lfs track "data/**/*.faiss"
git lfs track "data/**/*.npy"
git lfs track "data/**/*.csv"
git lfs track "data/images/**/*.jpg"

# Commit and push
git add .gitattributes
git add data/
git commit -m "Add data files with Git LFS"
git push origin main
```

#### Option B: Use Railway Volumes (For Large Files)

For larger datasets:

1. In Railway dashboard, go to your service
2. Click **Settings** > **Volumes**
3. Create a new volume mounted at `/app/data`
4. Upload your files using Railway CLI:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Upload data files
railway volume upload /app/data ./data
```

### 5. Deploy

Railway will automatically deploy your app. Monitor the deployment logs:

1. Go to your project in Railway dashboard
2. Click on **Deployments**
3. Watch the build and deployment logs

### 6. Access Your App

Once deployed:
- Your app will be available at a Railway-provided URL (e.g., `https://vibecheck-production.up.railway.app`)
- Find your URL in the **Settings** tab under **Domains**
- Optionally, add a custom domain

## Important Notes

### Memory and Resource Considerations

- **Model Loading**: Your app loads CLIP and Sentence Transformers models at startup, which requires significant memory (2-3GB)
- **Railway Free Tier**: Limited to 512MB RAM, which is **not sufficient** for this app
- **Recommended Plan**: Railway Pro ($20/month) with at least 2GB RAM

### Optimization Tips

1. **Reduce Workers**: The Procfile is configured with 2 workers and 2 threads. For memory constraints, reduce to:
   ```
   web: cd app && gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 1 --timeout 120 app:app
   ```

2. **Use CPU-Only Models**: Already configured with `faiss-cpu` instead of GPU version

3. **Lazy Loading**: Consider modifying [app/app.py](app/app.py:50-55) to load models on-demand rather than at startup

### Troubleshooting

**App crashes on startup:**
- Check logs for memory errors → Upgrade Railway plan
- Verify all data files are present in `/app/data`

**Models fail to load:**
- Check that PyTorch and dependencies installed correctly
- Review build logs for errors

**Database not found:**
- Verify `DB_PATH` environment variable
- Ensure database file is uploaded to correct path

**Images not displaying:**
- Check `IMAGE_DIR` path matches your uploads
- Verify image serving route in app.py:397-401

## Alternative: Using Docker

Railway also supports Docker deployments. Your project already has a Dockerfile at [docker/app/Dockerfile](docker/app/Dockerfile).

To use Docker instead:

1. Copy `docker/app/Dockerfile` to root:
   ```bash
   cp docker/app/Dockerfile ./
   ```

2. Railway will automatically detect and use the Dockerfile

3. This might provide better control over the build environment

## Cost Estimate

Based on your app requirements:
- **Railway Pro Plan**: $20/month
- **Estimated Resource Usage**: 2-3GB RAM, 1 vCPU
- **Estimated Cost**: ~$25-30/month (including resource usage beyond included credits)

## Support

If you encounter issues:
- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Check deployment logs in Railway dashboard

---

**Next Steps:**
1. Push code to GitHub
2. Create Railway project
3. Configure environment variables
4. Upload data files
5. Deploy and test!
