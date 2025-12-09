# Deploy VibeCheck to Fly.io

Quick guide to deploy VibeCheck on Fly.io's free tier.

## Prerequisites

1. **Install flyctl CLI**
   ```bash
   # macOS
   brew install flyctl

   # Linux
   curl -L https://fly.io/install.sh | sh

   # Windows
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
   ```

2. **Sign up and authenticate**
   ```bash
   flyctl auth signup
   # OR if you have an account
   flyctl auth login
   ```

## Deploy Steps

1. **Launch the app**
   ```bash
   flyctl launch
   ```

   When prompted:
   - App name: `vibecheck` (or your preferred name)
   - Region: Choose closest to you (default is usually good)
   - Add a Postgres database? **No**
   - Add Redis? **No**
   - Deploy now? **Yes**

2. **Monitor deployment**
   ```bash
   flyctl logs
   ```

3. **Check status**
   ```bash
   flyctl status
   ```

4. **Open your app**
   ```bash
   flyctl open
   ```

## Free Tier Limits

- **3 shared-cpu VMs** with 256MB RAM each (we use 512MB = 2 VMs worth)
- **3GB persistent storage** (not needed - we download from Google Drive)
- **160GB outbound data** per month

## Configuration Details

The app is configured in [fly.toml](fly.toml):
- **Memory**: 512MB (uses 2 of your 3 free VMs)
- **Auto-scaling**: Machines auto-stop when idle (saves resources)
- **Health checks**: 90s grace period for model loading
- **Data**: Downloads from Google Drive on startup

## Troubleshooting

**App crashes with OOM (Out of Memory)?**
- Upgrade to 1GB RAM: `flyctl scale memory 1024`
- This uses all 3 free VMs (256MB × 4 = 1GB)

**Models taking too long to load?**
- The lazy loading we implemented helps health checks pass
- First user will wait ~1-2 minutes for model loading
- Check logs: `flyctl logs`

**Need to redeploy?**
```bash
flyctl deploy
```

**Need to restart?**
```bash
flyctl apps restart vibecheck
```

## Cost Comparison

| Platform | Free Tier | Limitations |
|----------|-----------|-------------|
| **Fly.io** | 512MB RAM, 3 VMs | Auto-sleep when idle, 160GB bandwidth/mo |
| **Render** | 512MB RAM, 1 instance | 750 hrs/mo, sleeps after 15min idle |
| **Railway** | $5 credit/mo | ~170 hrs with 512MB, credit expires |

Fly.io is better for this app because:
- No sleep after idle (instant wake-up)
- More flexible resource allocation
- Better free tier for ML apps
