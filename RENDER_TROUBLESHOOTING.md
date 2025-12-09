# Render Deployment Troubleshooting

## Error: "No `project` table found in pyproject.toml"

**Symptom:**
```
error: No `project` table found in: `/opt/render/project/src/pyproject.toml`
==> Build failed
```

**Cause:** Render is trying to build your app as a **Python** application instead of using **Docker**.

### Fix Method 1: Change Runtime in Dashboard (Recommended)

1. Go to your service in Render dashboard
2. Click **Settings** tab
3. Find **"Build & Deploy"** section
4. Change these settings:
   - **Runtime**: `Docker` ⬅️ **IMPORTANT**
   - **Dockerfile Path**: `./Dockerfile`
   - **Docker Context**: `.`
   - **Docker Command**: Leave empty (uses CMD from Dockerfile)
5. Click **"Save Changes"**
6. Go to **"Manual Deploy"** tab
7. Click **"Deploy latest commit"**

### Fix Method 2: Delete and Recreate

If the runtime change doesn't work:

1. **Delete current service**:
   - Settings → Danger Zone → Delete Service

2. **Create new service** (Render will detect render.yaml):
   - Dashboard → "New +" → "Web Service"
   - Connect your repo
   - Wait for "Blueprint Detected" message
   - Click **"Apply"**
   - Service will be created with correct Docker runtime

### Fix Method 3: Use Render Blueprint (Infrastructure as Code)

1. **In Render Dashboard**, click "New +"
2. Select **"Blueprint"** (not "Web Service")
3. Connect your GitHub repository
4. Render will find and use `render.yaml`
5. Click **"Apply"**

---

## Error: Build Timeout

**Symptom:**
```
==> Build timed out after 15 minutes
```

**Cause:** Installing PyTorch and ML dependencies takes too long.

**Fix:**
1. **Pre-build Docker image** and push to Docker Hub:
   ```bash
   docker build -t yourusername/vibecheck:latest .
   docker push yourusername/vibecheck:latest
   ```

2. **Update render.yaml** to use pre-built image:
   ```yaml
   services:
     - type: web
       name: vibecheck-app
       runtime: image
       image:
         url: docker.io/yourusername/vibecheck:latest
   ```

3. **Redeploy**

---

## Error: Out of Memory During Build

**Symptom:**
```
Killed
error: Process killed
```

**Cause:** Not enough RAM during pip install.

**Fix:**
1. **Upgrade to Standard plan** (2GB minimum)
2. Or **use multi-stage build** in Dockerfile:
   ```dockerfile
   FROM python:3.11-slim as builder
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --user --no-cache-dir -r requirements.txt

   FROM python:3.11-slim
   COPY --from=builder /root/.local /root/.local
   # ... rest of Dockerfile
   ```

---

## Error: Models Fail to Load

**Symptom:**
```
RuntimeError: CUDA not available
```
OR
```
ModuleNotFoundError: No module named 'faiss'
```

**Fix:**
1. **Check requirements.txt** has `faiss-cpu` (not `faiss-gpu`):
   ```
   faiss-cpu>=1.13.0
   ```

2. **For CUDA errors**, ensure Dockerfile uses CPU-only PyTorch:
   ```
   torch>=2.9.1
   torchvision>=0.15.0
   ```
   (Don't specify +cpu or +cu118 - pip will choose correctly)

---

## Error: Data Files Not Found

**Symptom:**
```
FileNotFoundError: [Errno 2] No such file or directory: '/app/data/vibecheck.db'
```

**Cause:** Persistent disk not mounted or data not uploaded.

**Fix:**

1. **Verify disk is mounted**:
   - Settings → Disks → Check mount path is `/app/data`

2. **Upload data files**:
   - Go to Shell tab
   - Run: `ls -la /app/data`
   - If empty, upload files (see [scripts/upload-data-to-render.md](scripts/upload-data-to-render.md))

3. **Manual upload via Shell**:
   ```bash
   cd /app/data
   # Use "Upload File" button in shell interface
   ```

---

## Error: Port Binding Failed

**Symptom:**
```
Error: Failed to bind to $PORT
```

**Cause:** App not listening on the PORT environment variable.

**Fix:**

Check your Dockerfile CMD uses `$PORT` or hardcoded `8080`:
```dockerfile
# Option 1: Use hardcoded port (Render sets PORT=8080)
CMD gunicorn --chdir app --bind 0.0.0.0:8080 app:app

# Option 2: Use PORT env var
CMD gunicorn --chdir app --bind 0.0.0.0:$PORT app:app
```

In [app/app.py](app/app.py:411), ensure:
```python
port = int(os.getenv("PORT", 8080))
```

---

## Error: Health Check Failing

**Symptom:**
```
Health check failed
Service is unhealthy
```

**Cause:** App takes too long to start (loading ML models).

**Fix:**

1. **Increase health check timeout** in Dockerfile:
   ```dockerfile
   HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=3 \
       CMD curl -f http://localhost:8080/ || exit 1
   ```

2. **Or disable health check** temporarily:
   - Remove HEALTHCHECK line from Dockerfile
   - Redeploy

---

## Checking Your Configuration

### Verify Dockerfile is correct:

```bash
# Should be at project root
ls -la Dockerfile

# Should contain:
# - FROM python:3.11-slim
# - COPY requirements.txt
# - COPY app/ ./app/
# - CMD gunicorn ...
```

### Verify render.yaml is correct:

```bash
# Should be at project root
ls -la render.yaml

# Should contain:
# - runtime: docker
# - dockerfilePath: ./Dockerfile
# - plan: standard (minimum)
```

### Test Dockerfile locally:

```bash
# Build image
docker build -t vibecheck-test .

# Run container
docker run -p 8080:8080 vibecheck-test

# Test in browser
open http://localhost:8080
```

---

## Current Render Configuration Status

Based on your error logs, here's what needs to be fixed:

❌ **Runtime**: Currently set to "Python" (should be "Docker")
✅ **Dockerfile**: Present at root
✅ **render.yaml**: Present with correct config
❌ **Service Configuration**: Needs to be updated to use Docker

**Action Required**: Follow "Fix Method 1" above to change runtime to Docker.

---

## Getting Help

- **Render Docs**: https://render.com/docs/docker
- **Render Community**: https://community.render.com
- **Check Service Logs**: Dashboard → Your Service → Logs

---

## Quick Fix Checklist

- [ ] Verify Dockerfile exists at project root
- [ ] Verify render.yaml exists at project root
- [ ] Go to Render Settings
- [ ] Change Runtime to "Docker"
- [ ] Set Dockerfile Path to "./Dockerfile"
- [ ] Set Docker Context to "."
- [ ] Save changes
- [ ] Manual deploy latest commit
- [ ] Check logs for successful build
- [ ] Upload data files to /app/data
- [ ] Test your app!
