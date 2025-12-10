# Quick Start: Deploy VibeCheck to Hugging Face Spaces

**Goal**: Get your VibeCheck app live on Hugging Face in under 30 minutes!

## Prerequisites Checklist

- [ ] Hugging Face account ([sign up here](https://huggingface.co/join))
- [ ] Git and Git LFS installed
- [ ] Data files ready (vibecheck.db, vibecheck_index.faiss, meta_ids.npy, images/)

## 5-Step Quick Deployment

### Step 1: Install Git LFS (2 minutes)

```bash
# macOS
brew install git-lfs

# Ubuntu/Debian
sudo apt-get install git-lfs

# Windows
# Download from https://git-lfs.github.com/

# Initialize
git lfs install
```

### Step 2: Create Your Space (2 minutes)

1. Go to https://huggingface.co/spaces
2. Click **"Create new Space"**
3. Fill in:
   - **Name**: `vibecheck`
   - **SDK**: `Gradio`
   - **Hardware**: `CPU basic` (free, upgrade later if needed)
   - **Visibility**: Your choice
4. Click **"Create Space"**

### Step 3: Run Deployment Script (5 minutes)

```bash
cd /Users/iphone10/Desktop/VibeCheck

# Run the script
./deploy_to_hf.sh YOUR_HF_USERNAME vibecheck

# Example:
# ./deploy_to_hf.sh johndoe vibecheck
```

The script will:
- Clone your Space repository
- Copy necessary files
- Set up Git LFS
- Create proper file structure

### Step 4: Copy Data Files (10 minutes)

```bash
# After the script pauses, copy your data files:

# If using the scripts/vibecheck_full_output directory:
cp scripts/vibecheck_full_output/vibecheck.db hf_space_vibecheck/data/
cp scripts/vibecheck_full_output/vibecheck_index.faiss hf_space_vibecheck/data/
cp scripts/vibecheck_full_output/meta_ids.npy hf_space_vibecheck/data/
cp -r scripts/vibecheck_full_output/images hf_space_vibecheck/data/

# Or from your data directory:
cp data/vibecheck.db hf_space_vibecheck/data/
cp data/vibecheck_index.faiss hf_space_vibecheck/data/
cp data/meta_ids.npy hf_space_vibecheck/data/
cp -r data/images hf_space_vibecheck/data/

# Press Enter in the terminal when done
```

### Step 5: Push to Hugging Face (5 minutes)

```bash
cd hf_space_vibecheck

# Add all files
git add .

# Commit
git commit -m "Initial deployment of VibeCheck"

# Push (will take a few minutes for large files)
git push

# Enter your HF username and password/token when prompted
```

## What Happens Next?

1. **Build Process** (5-15 minutes)
   - Hugging Face builds your Space
   - Downloads and installs dependencies
   - Loads your data files
   - Watch progress at: `https://huggingface.co/spaces/YOUR_USERNAME/vibecheck`

2. **App Goes Live** 🎉
   - Automatically launches when build completes
   - Access at: `https://huggingface.co/spaces/YOUR_USERNAME/vibecheck`
   - Share the link with anyone!

## Test Your Deployment

Once live, try these queries:

1. **Text only**: "cozy romantic lighting with vintage furniture"
2. **Image only**: Upload a restaurant photo
3. **Hybrid**: Use both text and image together

## Common Issues & Quick Fixes

### Issue: "Git LFS quota exceeded"
**Fix**: Upgrade to HF Pro ($9/month) or use smaller dataset

### Issue: "Build failed - Out of memory"
**Fix**:
1. Go to your Space page
2. Settings → Hardware
3. Upgrade to "CPU upgrade" (~$0.03/hour)

### Issue: "Database not found"
**Fix**: Check files are in correct location:
```bash
cd hf_space_vibecheck
tree -L 2 data/
# Should show:
# data/
# ├── vibecheck.db
# ├── vibecheck_index.faiss
# ├── meta_ids.npy
# └── images/
```

### Issue: "CLIP model download timeout"
**Fix**: Add to `app.py` (line 15):
```python
import os
os.environ['TRANSFORMERS_CACHE'] = '/tmp/models'
```

## Alternative: Manual Upload (If Script Fails)

If the script doesn't work, upload manually:

1. On your Space page, click **"Files"**
2. Click **"Add file"** → **"Upload files"**
3. Upload these files:
   - `app_gradio.py` (rename to `app.py`)
   - `requirements_hf.txt` (rename to `requirements.txt`)
   - `.gitattributes_hf` (rename to `.gitattributes`)
4. Create `data/` folder
5. Upload data files to `data/`

## Hardware Recommendations

### Free Tier (CPU basic)
- ✅ Good for: Testing, demos, low traffic
- ❌ Limitations: Slower inference (3-5s per query)

### CPU Upgrade (~$3/day)
- ✅ Good for: Production, moderate traffic
- ⚡ Speed: 1-2s per query

### T4 Small GPU (~$15/day)
- ✅ Good for: High traffic, best performance
- ⚡ Speed: <1s per query
- 💡 Tip: Only enable when needed (Spaces auto-sleep)

## Cost Optimization Tips

1. **Use free tier** for initial testing
2. **Upgrade temporarily** for demos/presentations
3. **Enable auto-sleep** (Settings → Sleep time)
4. **Monitor usage** (Settings → Analytics)

## Next Steps After Deployment

1. **Customize UI**: Edit `app.py` to modify interface
2. **Add analytics**: Track usage in Space settings
3. **Share**: Post on Twitter, LinkedIn with link
4. **Monitor**: Check logs regularly for errors
5. **Update**: Push changes with `git push`

## Getting Help

- 📖 Full guide: [HUGGINGFACE_DEPLOYMENT.md](HUGGINGFACE_DEPLOYMENT.md)
- 💬 Ask questions: [Hugging Face Forums](https://discuss.huggingface.co/)
- 🐛 Report issues: [GitHub Issues](https://github.com/manav-ar/VibeCheck/issues)
- 📧 HF Support: support@huggingface.co

## Useful Commands

```bash
# Check Git LFS files
git lfs ls-files

# Check file sizes
du -sh hf_space_vibecheck/data/*

# View build logs
# (Go to Space page → "Build logs" tab)

# Update Space after changes
cd hf_space_vibecheck
git add .
git commit -m "Update description"
git push
```

## Success Checklist

After deployment, verify:

- [ ] Space builds without errors
- [ ] App loads at your Space URL
- [ ] Text search returns results
- [ ] Image upload works
- [ ] Restaurant images display correctly
- [ ] Results are relevant to queries

---

**Congratulations!** 🎉 Your VibeCheck app is now live on Hugging Face!

Share your Space: `https://huggingface.co/spaces/YOUR_USERNAME/vibecheck`
