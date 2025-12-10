# Deploying VibeCheck to Hugging Face Spaces

This guide explains how to deploy VibeCheck to Hugging Face Spaces using Gradio.

## Prerequisites

1. **Hugging Face Account**: Sign up at [huggingface.co](https://huggingface.co/)
2. **Data Files**: You need the following files from your Google Drive (see [DATA_SETUP.md](DATA_SETUP.md)):
   - `vibecheck.db` (SQLite database)
   - `vibecheck_index.faiss` (FAISS index)
   - `meta_ids.npy` (restaurant ID mappings)
   - `images/` directory (restaurant photos)

## Step 1: Create a New Space

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces)
2. Click **"Create new Space"**
3. Configure your Space:
   - **Name**: `vibecheck` (or your preferred name)
   - **License**: MIT
   - **SDK**: Select **Gradio**
   - **Hardware**:
     - For testing: **CPU basic (free)**
     - For production: **CPU upgrade** or **T4 small GPU** (recommended)
   - **Visibility**: Public or Private

4. Click **"Create Space"**

## Step 2: Clone the Space Repository

After creating the Space, clone it to your local machine:

```bash
# Install git-lfs (required for large files)
# On macOS:
brew install git-lfs

# On Ubuntu/Debian:
sudo apt-get install git-lfs

# On Windows: download from https://git-lfs.github.com/

# Initialize git-lfs
git lfs install

# Clone your Space
git clone https://huggingface.co/spaces/YOUR_USERNAME/vibecheck
cd vibecheck
```

## Step 3: Prepare Files for Upload

From your VibeCheck project directory:

```bash
# Copy the Gradio app
cp app_gradio.py <path-to-space>/app.py

# Copy requirements
cp requirements_hf.txt <path-to-space>/requirements.txt

# Create data directory
mkdir -p <path-to-space>/data
```

## Step 4: Upload Data Files

### Option A: Upload via Git LFS (Recommended for < 50GB)

```bash
cd <path-to-space>

# Track large files with Git LFS
git lfs track "*.faiss"
git lfs track "*.npy"
git lfs track "*.db"
git lfs track "data/images/*"

# Add .gitattributes
git add .gitattributes

# Copy your data files
cp /path/to/your/data/vibecheck.db data/
cp /path/to/your/data/vibecheck_index.faiss data/
cp /path/to/your/data/meta_ids.npy data/
cp -r /path/to/your/data/images data/

# Add and commit
git add app.py requirements.txt data/
git commit -m "Initial deployment with data files"

# Push to Hugging Face
git push
```

### Option B: Upload via Hugging Face Web Interface

1. Go to your Space page on Hugging Face
2. Click **"Files"** tab
3. Click **"Add file"** → **"Upload files"**
4. Upload files one by one or in batches:
   - `app.py` (your `app_gradio.py` renamed)
   - `requirements.txt`
   - Create `data/` folder and upload:
     - `vibecheck.db`
     - `vibecheck_index.faiss`
     - `meta_ids.npy`
     - `images/` (all image files)

### Option C: Use Hugging Face CLI

```bash
# Install Hugging Face CLI
pip install huggingface_hub

# Login
huggingface-cli login

# Upload files
huggingface-cli upload YOUR_USERNAME/vibecheck app.py
huggingface-cli upload YOUR_USERNAME/vibecheck requirements.txt
huggingface-cli upload YOUR_USERNAME/vibecheck data/ --repo-type=space
```

## Step 5: Configure Space Settings (Optional)

Create a `README.md` in your Space:

```markdown
---
title: VibeCheck Restaurant Discovery
emoji: 🍽️
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 5.12.0
app_file: app.py
pinned: false
license: mit
---

# VibeCheck: Restaurant Discovery by Ambience

Find restaurants based on their vibe and atmosphere using AI-powered multimodal search!

## Features

- 📝 Text-based ambience search
- 🖼️ Image-based similarity search
- 🔄 Hybrid text + image search
- 🤖 Powered by CLIP, Sentence-BERT, and FAISS

## Usage

1. Describe the restaurant vibe you're looking for
2. Or upload a reference image
3. Or combine both for better results!
```

## Step 6: Wait for Build

After pushing files:

1. Go to your Space page
2. Watch the build logs in the **"Build logs"** section
3. First build may take 5-15 minutes (downloading models, installing dependencies)
4. Once complete, your app will be live!

## Step 7: Test Your Deployment

1. Visit your Space URL: `https://huggingface.co/spaces/YOUR_USERNAME/vibecheck`
2. Try a text query: "cozy romantic lighting with vintage furniture"
3. Upload a test image
4. Verify results are displayed correctly

## Troubleshooting

### Build Fails - Out of Memory

**Solution**: Upgrade to a larger hardware tier:
- Go to Space Settings → Hardware
- Upgrade to "CPU upgrade" or "T4 small GPU"

### Models Download Timeout

**Solution**: Add `.env` file to cache models:

```bash
# In your Space root
echo "TRANSFORMERS_CACHE=/tmp/models" > .env
```

### Data Files Not Found

**Error**: `Database not found at data/vibecheck.db`

**Solution**: Ensure files are in correct location:
```
your-space/
├── app.py
├── requirements.txt
└── data/
    ├── vibecheck.db
    ├── vibecheck_index.faiss
    ├── meta_ids.npy
    └── images/
        ├── restaurant_1.jpg
        ├── restaurant_2.jpg
        └── ...
```

### Images Not Loading

**Solution**: Verify image paths in database match files in `data/images/`

```python
# Check database
sqlite3 data/vibecheck.db "SELECT local_filename FROM vibe_photos LIMIT 5;"

# Ensure these files exist in data/images/
```

### Slow Performance

**Solutions**:
1. **Upgrade hardware**: Use T4 GPU for faster inference
2. **Reduce index size**: Use a subset of restaurants
3. **Enable caching**: Add model caching in `app.py`

```python
# Add to app.py after imports
import os
os.environ['TRANSFORMERS_CACHE'] = '/tmp/models'
```

## Storage Limits

Hugging Face Spaces storage limits:
- **Free tier**: 50GB per Space
- **Pro tier**: 1TB per Space

If your data exceeds limits:
1. Compress images: `mogrify -resize 800x800 data/images/*.jpg`
2. Use external storage (S3, Cloudflare R2) for images
3. Reduce number of restaurants in index

## Cost Considerations

### Free Tier
- CPU basic hardware
- Sufficient for demos and testing
- May have slower response times

### Paid Tiers (Recommended for Production)
- **CPU upgrade**: ~$0.03/hour
- **T4 small GPU**: ~$0.60/hour (much faster)
- Only charged when Space is running
- Spaces auto-sleep after inactivity

## Advanced: Using External Storage

For very large datasets, store images externally:

### 1. Upload Images to Cloudflare R2 or S3

```bash
# Example with Cloudflare R2
rclone copy data/images/ r2:vibecheck-images/
```

### 2. Update Database URLs

```python
# Update photo URLs in database to point to CDN
import sqlite3
conn = sqlite3.connect('data/vibecheck.db')
cursor = conn.cursor()

cursor.execute("""
    UPDATE vibe_photos
    SET photo_url = 'https://your-cdn.com/images/' || local_filename
""")
conn.commit()
```

### 3. Modify app.py to Load from URL

```python
from PIL import Image
import requests
from io import BytesIO

def load_image(url):
    response = requests.get(url)
    return Image.open(BytesIO(response.content))
```

## Updating Your Space

To update your deployed app:

```bash
cd <path-to-space>

# Make changes to app.py or other files

# Commit and push
git add .
git commit -m "Update: description of changes"
git push

# Space will rebuild automatically
```

## Monitoring and Logs

1. **View logs**: Space page → **"Build logs"** or **"Runtime logs"**
2. **Check metrics**: Settings → **"Analytics"**
3. **Monitor usage**: Spaces dashboard shows usage stats

## Security Best Practices

1. **Don't commit secrets**: Use Hugging Face Spaces secrets for API keys
   - Settings → **"Repository secrets"**
   - Access in code: `os.environ.get('SECRET_NAME')`

2. **Rate limiting**: Add rate limiting for public Spaces

```python
# In app.py
demo.launch(
    max_threads=10,  # Limit concurrent users
    enable_queue=True
)
```

3. **Input validation**: Validate user inputs

```python
def search_restaurants(query_text, query_image, top_k):
    # Validate inputs
    if len(query_text) > 500:
        return "Query too long!", []
    if top_k > 20:
        top_k = 20
    # ... rest of function
```

## Alternative: Gradio on Custom Domain

You can also deploy to your own server and use Gradio's share feature:

```python
# In app.py
demo.launch(
    share=True,  # Creates public link
    server_name="0.0.0.0",
    server_port=7860
)
```

## Next Steps

1. **Customize UI**: Modify Gradio interface in `app.py`
2. **Add features**:
   - Save favorite restaurants
   - User feedback system
   - Analytics tracking
3. **Optimize performance**:
   - Cache frequently queried embeddings
   - Use GPU hardware
   - Implement result pagination

## Resources

- [Hugging Face Spaces Documentation](https://huggingface.co/docs/hub/spaces)
- [Gradio Documentation](https://gradio.app/docs/)
- [Git LFS Documentation](https://git-lfs.github.com/)
- [VibeCheck GitHub](https://github.com/manav-ar/VibeCheck)

## Support

If you encounter issues:
1. Check Space build logs
2. Review this troubleshooting guide
3. Open an issue on [GitHub](https://github.com/manav-ar/VibeCheck/issues)
4. Ask in [Hugging Face Forums](https://discuss.huggingface.co/)

---

**Happy Deploying!** 🚀
