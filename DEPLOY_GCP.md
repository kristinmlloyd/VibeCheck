# Deploy VibeCheck to Google Cloud Run (FREE)

Google Cloud Run is perfect for this app - serverless, generous free tier, and no credit card required for the free tier!

## Why Google Cloud Run?

✅ **Free tier**: 2 million requests/month, 360,000 GB-seconds of memory
✅ **No credit card required** for free tier (until you exceed limits)
✅ **Serverless**: Auto-scales from 0 to millions
✅ **2GB RAM available** on free tier - perfect for your models
✅ **Pay only when used**: $0 when idle
✅ **Built-in HTTPS**: Automatic SSL certificates

## Prerequisites

1. **Google Cloud account**
   - Go to https://console.cloud.google.com
   - Sign up with your Gmail (no credit card for free tier)

2. **Install Google Cloud CLI**
   ```bash
   # macOS
   brew install google-cloud-sdk

   # Or download from: https://cloud.google.com/sdk/docs/install
   ```

3. **Login and setup**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

## Quick Deploy (3 commands!)

### Method 1: Deploy directly from source (Easiest)

```bash
# 1. Build and deploy in one command
gcloud run deploy vibecheck \
  --source . \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 1 \
  --timeout 900 \
  --max-instances 1 \
  --allow-unauthenticated \
  --set-env-vars FLASK_ENV=production,OUTPUT_DIR=/app/data,DB_PATH=/app/data/vibecheck.db,IMAGE_DIR=/app/data/images,FAISS_PATH=/app/data/vibecheck_index.faiss,META_PATH=/app/data/meta_ids.npy,VIBE_MAP_CSV=/app/data/vibe_map.csv,OMP_NUM_THREADS=1,MKL_NUM_THREADS=1,PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128,TOKENIZERS_PARALLELISM=false

# 2. Wait for deployment (takes ~10 minutes first time)

# 3. Your app will be live at the URL shown!
```

### Method 2: Using Cloud Build (More control)

```bash
# 1. Submit build
gcloud builds submit --config cloudbuild.yaml

# 2. Done! Check your deployment
gcloud run services list
```

## Configuration Details

**Memory**: 2GB (free tier allows up to 2GB)
**CPU**: 1 vCPU (free tier allows 1 CPU)
**Timeout**: 900s (15 minutes) - enough for data download + model loading
**Max instances**: 1 (to stay in free tier)
**Cold start**: ~2-3 minutes first request (downloading Google Drive data + loading models)

## Environment Variables

All environment variables are set automatically:
- `FLASK_ENV=production`
- `OUTPUT_DIR=/app/data`
- `DB_PATH=/app/data/vibecheck.db`
- `IMAGE_DIR=/app/data/images`
- `FAISS_PATH=/app/data/vibecheck_index.faiss`
- `META_PATH=/app/data/meta_ids.npy`
- `VIBE_MAP_CSV=/app/data/vibe_map.csv`
- Memory optimization env vars (OMP_NUM_THREADS, etc.)

## Monitoring & Logs

```bash
# View logs
gcloud run services logs read vibecheck --region us-central1

# Check service details
gcloud run services describe vibecheck --region us-central1

# See metrics
# Go to: https://console.cloud.google.com/run
```

## Cost Estimate (Free Tier)

Cloud Run **free tier includes**:
- 2 million requests/month
- 360,000 GB-seconds of memory
- 180,000 vCPU-seconds

**Your app usage**:
- Memory: 2GB × 15min startup = ~1,800 GB-seconds per cold start
- You can have ~200 cold starts/month **FREE**
- If app stays warm: virtually unlimited requests FREE

**After free tier**: ~$0.024/hour when running = ~$18/month if always on

## Tips to Stay Free

1. **Let it scale to zero** - Don't keep always warm, let it sleep when idle
2. **Single instance** - `--max-instances 1` (already configured)
3. **Use lazy loading** - Already implemented in your app
4. **Monitor usage** - Check Cloud Console billing dashboard

## Optimizations Already Applied

✅ **Lazy loading** - Models load on first request, not startup
✅ **Single Gunicorn worker** - Saves memory
✅ **Google Drive data** - No persistent storage needed
✅ **Memory limits** - Environment variables configured
✅ **900s timeout** - Enough time for first request

## Troubleshooting

**Build timeout?**
```bash
# Increase build timeout
gcloud config set builds/timeout 1800
```

**Out of memory?**
```bash
# Upgrade to 4GB (still free tier eligible, but uses more quota)
gcloud run services update vibecheck --memory 4Gi
```

**Cold starts too slow?**
```bash
# Keep 1 instance always warm (costs ~$18/month)
gcloud run services update vibecheck --min-instances 1
```

**Google Drive download fails?**
- Check logs: `gcloud run services logs read vibecheck`
- Verify Google Drive links are publicly accessible
- Try deploying again (sometimes gdown has rate limits)

## Update/Redeploy

```bash
# After making code changes
git add .
git commit -m "Update app"
git push

# Redeploy
gcloud run deploy vibecheck --source .
```

## Custom Domain (Optional)

```bash
# Map your own domain (free!)
gcloud run domain-mappings create \
  --service vibecheck \
  --domain yourdomain.com \
  --region us-central1
```

## Cleanup

```bash
# Delete the service
gcloud run services delete vibecheck --region us-central1
```

## Comparison with Other Platforms

| Platform | Free Tier | RAM | Cold Starts | Credit Card |
|----------|-----------|-----|-------------|-------------|
| **Cloud Run** | 2M requests/mo | 2GB | ~2-3min | No* |
| Render | 750hrs/mo | 512MB | 1min | No |
| Fly.io | Limited | 512MB | <1min | Yes |
| AWS EB | None | Custom | N/A | Yes |

*Credit card not required unless you exceed free tier limits

**Recommendation**: Cloud Run is the best free option for this app!
