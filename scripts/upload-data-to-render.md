# Uploading Data to Render Persistent Disk

After your Render service is deployed, you need to upload your data files to the persistent disk.

## Method 1: Using Render Shell (Web Interface)

### Step-by-step:

1. **Go to your Render service**
   - Dashboard → Select your service (`vibecheck-app`)

2. **Open Shell tab**
   - Click **Shell** in the top navigation

3. **Verify disk is mounted**
   ```bash
   ls -lah /app/data
   # Should show your mounted disk
   ```

4. **Upload files one by one**
   - Use the **"Upload File"** button in the shell interface
   - Navigate to `/app/data` before uploading
   - Upload these files:
     - `vibecheck.db`
     - `vibecheck_index.faiss`
     - `meta_ids.npy`
     - `vibe_map.csv`

5. **Create images directory**
   ```bash
   mkdir -p /app/data/images
   ```

6. **Upload images**
   - Click **"Upload File"** again
   - Select destination: `/app/data/images`
   - Upload all restaurant images (this may take a while)

7. **Verify uploads**
   ```bash
   ls -lah /app/data/
   ls -lah /app/data/images/ | head -20
   ```

### Pros:
- No additional tools needed
- Simple web interface
- Works from any browser

### Cons:
- Slow for large files
- Manual process
- Can timeout for very large uploads

---

## Method 2: Using Render CLI (For Large Datasets)

### Prerequisites:
```bash
# Install Render CLI
npm install -g @render/cli
# OR using Homebrew on Mac
brew install render

# Authenticate
render login
```

### Upload data:

1. **List your services**
   ```bash
   render services list
   ```

2. **SSH into your service**
   ```bash
   render ssh <your-service-id>
   ```

3. **Once connected, use `scp` or `rsync` from another terminal**

   From your local machine:
   ```bash
   # This requires setting up SSH keys with Render
   # See: https://render.com/docs/ssh-keys

   # Upload database
   scp data/vibecheck.db render:/app/data/

   # Upload FAISS index
   scp data/vibecheck_index.faiss render:/app/data/

   # Upload metadata
   scp data/meta_ids.npy render:/app/data/
   scp data/vibe_map.csv render:/app/data/

   # Upload images directory
   scp -r data/images/ render:/app/data/images/
   ```

### Pros:
- Faster for large files
- Can automate with scripts
- Uses compression

### Cons:
- Requires CLI installation
- More complex setup
- Need SSH keys configured

---

## Method 3: Build Data Into Docker Image (Not Recommended)

Only use this if your data is small (<500MB total).

1. **Comment out data exclusions in `.dockerignore`**
   ```dockerfile
   # Comment these lines:
   # data/
   # *.db
   # *.faiss
   ```

2. **Add data copy to Dockerfile**
   ```dockerfile
   # Add before CMD
   COPY data/ /app/data/
   ```

3. **Redeploy**
   ```bash
   git add .dockerignore Dockerfile
   git commit -m "Include data in Docker image"
   git push origin main
   ```

### Pros:
- Automatic deployment
- No manual upload needed

### Cons:
- Very slow builds (large image)
- Expensive bandwidth
- Not recommended for >500MB
- Makes updates harder

---

## Method 4: Use Cloud Storage (Advanced)

For very large datasets, store data externally and download on startup.

### Using AWS S3:

1. **Upload data to S3**
   ```bash
   aws s3 sync data/ s3://your-bucket/vibecheck-data/
   ```

2. **Add download script to Dockerfile**
   ```dockerfile
   # Install AWS CLI
   RUN apt-get update && apt-get install -y awscli

   # Add startup script
   COPY scripts/download-data.sh /app/
   RUN chmod +x /app/download-data.sh

   # Modify CMD to download first
   CMD ["/bin/bash", "-c", "/app/download-data.sh && gunicorn ..."]
   ```

3. **Create `scripts/download-data.sh`**
   ```bash
   #!/bin/bash
   set -e

   echo "Downloading data from S3..."

   # Check if data already exists (persistent disk)
   if [ -f "/app/data/vibecheck.db" ]; then
       echo "Data already exists, skipping download"
       exit 0
   fi

   # Download from S3
   aws s3 sync s3://your-bucket/vibecheck-data/ /app/data/

   echo "Data download complete"
   ```

4. **Add AWS credentials as Render environment variables**
   ```
   AWS_ACCESS_KEY_ID=your_key
   AWS_SECRET_ACCESS_KEY=your_secret
   AWS_DEFAULT_REGION=us-east-1
   ```

### Pros:
- Fast initial deployment
- Easy to update data
- Good for very large datasets
- Versioning possible

### Cons:
- Additional cloud costs
- More complex setup
- Requires AWS account

---

## Recommended Approach by Data Size

| Data Size | Method | Reason |
|-----------|--------|--------|
| < 100MB | Method 3 (Build into image) | Simple, fast |
| 100MB - 2GB | Method 1 (Web shell) | No setup needed |
| 2GB - 10GB | Method 2 (CLI) | Faster uploads |
| > 10GB | Method 4 (Cloud storage) | Best performance |

---

## Verification After Upload

After uploading by any method, verify your data:

```bash
# SSH into Render service
render ssh <service-id>

# Check files
ls -lah /app/data/
# Should show:
# - vibecheck.db
# - vibecheck_index.faiss
# - meta_ids.npy
# - vibe_map.csv
# - images/

# Check database
sqlite3 /app/data/vibecheck.db "SELECT COUNT(*) FROM restaurants;"

# Check FAISS index size
du -h /app/data/vibecheck_index.faiss

# Check image count
find /app/data/images -type f | wc -l
```

## Restart Your Service

After uploading all data:

1. Go to Render Dashboard
2. Click **Manual Deploy** → **Deploy latest commit**
3. Or trigger restart: **Settings** → **Restart**

Your app should now load successfully with all data!

---

## Troubleshooting

**Upload fails/times out:**
- Try uploading smaller batches
- Use Method 2 (CLI) instead
- Check your internet connection

**Files disappear after restart:**
- Verify persistent disk is mounted
- Check you uploaded to `/app/data` (not `/data` or other path)

**Permission denied:**
- Files should be owned by `render` user
- Run: `chown -R render:render /app/data`

**Out of disk space:**
- Check disk usage: `df -h /app/data`
- Increase disk size in Render dashboard

---

**Need help?** Check [RENDER_DEPLOYMENT.md](../RENDER_DEPLOYMENT.md) or Render docs.
