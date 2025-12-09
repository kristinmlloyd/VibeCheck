# Render Deployment Quick Start

## TL;DR - Deploy in 10 Minutes

Your app is already Dockerized and ready for Render! Follow these steps:

### 1. Prepare Dockerfile (Choose One)

**Option A: Simple (Recommended)**
```bash
cp Dockerfile.render Dockerfile
```

**Option B: Use existing Poetry-based**
```bash
cp docker/app/Dockerfile Dockerfile
```

### 2. Push to GitHub

```bash
git add Dockerfile render.yaml
git commit -m "Add Render deployment configuration"
git push origin main
```

### 3. Deploy on Render

1. Go to https://render.com
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repo
4. Render auto-detects `render.yaml` ✨
5. Click **"Apply"**

### 4. Upload Data Files

**Via Render Shell:**
1. Dashboard → Your Service → **Shell**
2. Navigate: `cd /app/data`
3. Upload files via shell interface

**OR use this helper script:**
```bash
./scripts/prepare-render-deploy.sh
```

---

## Key Configuration

### Minimum Requirements

- **Instance Type**: Standard (2GB RAM)
- **Cost**: ~$25/month
- **Persistent Disk**: 10GB at `/app/data`

### Important Environment Variables

Already set in `render.yaml`:
```
PORT=8080
FLASK_ENV=production
DB_PATH=/app/data/vibecheck.db
IMAGE_DIR=/app/data/images
```

### Data Files Required

Upload to `/app/data/`:
- `vibecheck.db` (SQLite database)
- `vibecheck_index.faiss` (FAISS index)
- `meta_ids.npy` (Restaurant ID mapping)
- `vibe_map.csv` (UMAP coordinates)
- `images/` (Restaurant photos)

---

## What's Included

✅ `render.yaml` - Infrastructure as code
✅ `Dockerfile.render` - Optimized for Render
✅ `.dockerignore` - Optimized builds
✅ `requirements.txt` - All dependencies
✅ Health checks configured
✅ Gunicorn for production serving

---

## Troubleshooting

**App won't start?**
- Check you're using Standard plan (2GB RAM minimum)
- View logs: Dashboard → Your Service → Logs

**Models fail to load?**
- Verify `faiss-cpu` (not `faiss-gpu`) in requirements.txt
- Startup takes 2-3 minutes - be patient!

**Data not found?**
- Verify persistent disk mounted at `/app/data`
- Check files uploaded via Shell: `ls -lah /app/data`

**Images broken?**
- Ensure images uploaded to `/app/data/images`
- Check route: `/images/<filename>` in app

---

## Your URLs

After deployment:
- **App URL**: `https://vibecheck-app-xxxx.onrender.com`
- **Health Check**: `https://your-app.onrender.com/`
- **API Test**: `https://your-app.onrender.com/api/vibe-stats`

---

## Cost Breakdown

| Item | Cost |
|------|------|
| Standard instance (2GB) | $25/mo |
| Persistent disk (10GB) | $1/mo |
| **Total** | **~$26/mo** |

For better performance: Standard Plus (4GB) = $85/month

---

## Need More Help?

📖 **Full Guide**: [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md)
🛠️ **Render Docs**: https://render.com/docs
💬 **Community**: https://community.render.com

---

**Ready?** Run the helper script:
```bash
./scripts/prepare-render-deploy.sh
```

Then follow the prompts! 🚀
