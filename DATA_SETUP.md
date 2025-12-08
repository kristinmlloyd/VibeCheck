# Data Setup Guide for Docker

This guide explains how to set up the data files for the VibeCheck Docker deployment.

## Required Data Files

The application requires the following data files from Google Drive:

- **Database**: `vibecheck.db` (SQLite database with restaurants, reviews, vibes)
- **Images**: Directory with restaurant photos
- **FAISS Index**: `vibecheck_index.faiss` (pre-computed embeddings index)
- **Metadata**: `meta_ids.npy` (restaurant ID mappings for FAISS)
- **Vibe Map**: `vibe_map.csv` (UMAP coordinates and cluster data)

## Directory Structure

Create the following directory structure in your project root:

```
VibeCheck-git/
├── data/
│   ├── vibecheck.db
│   ├── vibecheck_index.faiss
│   ├── meta_ids.npy
│   ├── vibe_map.csv
│   └── images/
│       ├── restaurant_1.jpg
│       ├── restaurant_2.jpg
│       └── ...
```

## Setup Steps

### 1. Create Data Directory

```bash
mkdir -p data/images
```

### 2. Download Files from Google Drive

Download all files from the shared Google Drive link:
https://drive.google.com/drive/folders/1EXlgII9BrqfkYYuDljkOHK8dXKCDldb6?usp=sharing

### 3. Place Files in Correct Locations

```bash
# From your downloads folder (adjust path as needed)
cd ~/Downloads/vibecheck_data

# Copy database
cp vibecheck.db /path/to/VibeCheck-git/data/

# Copy FAISS index and metadata
cp vibecheck_index.faiss /path/to/VibeCheck-git/data/
cp meta_ids.npy /path/to/VibeCheck-git/data/

# Copy vibe map CSV
cp vibe_map.csv /path/to/VibeCheck-git/data/

# Copy all images
cp -r images/* /path/to/VibeCheck-git/data/images/
```

### 4. Verify Data Structure

```bash
cd /path/to/VibeCheck-git
tree -L 2 data/
```

Expected output:
```
data/
├── vibecheck.db
├── vibecheck_index.faiss
├── meta_ids.npy
├── vibe_map.csv
└── images/
    ├── restaurant_1.jpg
    ├── restaurant_2.jpg
    └── ...
```

### 5. Check File Sizes

```bash
ls -lh data/
```

Expected approximate sizes:
- `vibecheck.db`: ~50-100 MB
- `vibecheck_index.faiss`: ~200-500 MB
- `meta_ids.npy`: ~1-5 MB
- `vibe_map.csv`: ~100 KB
- `images/`: ~500 MB - 2 GB (depending on number of restaurants)

## Alternative: Using Existing Output Directory

If you already have `scripts/vibecheck_full_output/` with all the data:

```bash
# Create symbolic link
ln -s scripts/vibecheck_full_output data

# Or copy the files
mkdir -p data
cp scripts/vibecheck_full_output/vibecheck.db data/
cp scripts/vibecheck_full_output/vibecheck_index.faiss data/
cp scripts/vibecheck_full_output/meta_ids.npy data/
cp scripts/vibecheck_full_output/vibe_map.csv data/
cp -r scripts/vibecheck_full_output/images data/
```

## Docker Volume Mounting

The `docker-compose.yml` is configured to mount the `data/` directory as a read-only volume inside containers:

```yaml
volumes:
  - ./data:/app/data:ro
```

This means:
- Data files are NOT copied into the Docker image (keeping images small)
- All containers share the same data directory
- Data can be updated without rebuilding images
- `:ro` flag ensures data integrity (read-only)

## Troubleshooting

### Missing Files Error

If you see errors like "File not found: /app/data/vibecheck.db":

1. Check that files exist: `ls -la data/`
2. Verify Docker compose is running: `docker-compose ps`
3. Check volume mounts: `docker-compose config`
4. Restart services: `docker-compose restart`

### Permission Issues

If you encounter permission errors:

```bash
# Ensure files are readable
chmod -R 755 data/
chmod 644 data/*.db data/*.faiss data/*.npy data/*.csv
```

### Large Image Upload

If the images directory is very large (>2GB), consider:

1. Using only a subset of images for testing
2. Compressing images: `mogrify -resize 800x800 data/images/*.jpg`
3. Using remote storage (S3, Cloud Storage) for production

## Production Considerations

For production deployments:

1. **Cloud Storage**: Store images on S3/GCS and update image URLs in database
2. **Database**: Use PostgreSQL instead of SQLite for better concurrency
3. **FAISS Index**: Use GPU-accelerated FAISS for faster search
4. **CDN**: Serve images through a CDN for better performance
5. **Backup**: Regular backups of database and indices

## Next Steps

After setting up data files:

1. Build Docker images: `docker-compose build`
2. Start services: `docker-compose up`
3. Access application: `http://localhost:5000`
