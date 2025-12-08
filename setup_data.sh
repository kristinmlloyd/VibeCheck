#!/bin/bash
# Simple data reorganization for Docker deployment
# This script reorganizes existing data files into the Docker-expected structure

set -e

echo "=========================================="
echo "VibeCheck Data Reorganization"
echo "=========================================="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check which database to use
if [ -f "data/restaurants_info/restaurants.db" ]; then
    DB_SOURCE="data/restaurants_info/restaurants.db"
elif [ -f "data/restaurants_info/restaurants_sample.db" ]; then
    DB_SOURCE="data/restaurants_info/restaurants_sample.db"
    echo -e "${YELLOW}⚠ Using sample database (restaurants_sample.db)${NC}"
else
    echo -e "${RED}✗ No database file found!${NC}"
    exit 1
fi

echo "Creating flat data structure for Docker..."
echo ""

# Create symlinks instead of copying (saves space)
echo "Creating symbolic links..."

# Database
if [ ! -f "data/vibecheck.db" ]; then
    ln -s "../${DB_SOURCE#data/}" data/vibecheck.db
    echo -e "${GREEN}✓${NC} Database: data/vibecheck.db → $DB_SOURCE"
fi

# FAISS index
if [ ! -f "data/vibecheck_index.faiss" ]; then
    ln -s "../data/embeddings/vibecheck_index.faiss" data/vibecheck_index.faiss
    echo -e "${GREEN}✓${NC} FAISS Index: data/vibecheck_index.faiss → data/embeddings/vibecheck_index.faiss"
fi

# Metadata
if [ ! -f "data/meta_ids.npy" ]; then
    ln -s "../data/restaurants_info/meta_ids.npy" data/meta_ids.npy
    echo -e "${GREEN}✓${NC} Metadata: data/meta_ids.npy → data/restaurants_info/meta_ids.npy"
fi

# Vibe map CSV
if [ ! -f "data/vibe_map.csv" ]; then
    if [ -f "data/processed/vibe_map.csv" ]; then
        ln -s "../data/processed/vibe_map.csv" data/vibe_map.csv
        echo -e "${GREEN}✓${NC} Vibe Map: data/vibe_map.csv → data/processed/vibe_map.csv"
    elif [ -f "vibe_map.csv" ]; then
        ln -s "../../vibe_map.csv" data/vibe_map.csv
        echo -e "${GREEN}✓${NC} Vibe Map: data/vibe_map.csv → ./vibe_map.csv"
    else
        echo -e "${YELLOW}⚠${NC} Vibe Map: Not found (will be generated on startup)"
    fi
fi

# Images directory
if [ ! -d "data/images" ] || [ ! "$(ls -A data/images 2>/dev/null)" ]; then
    if [ -d "data/images/restaurant_images" ]; then
        echo -e "${GREEN}✓${NC} Images: Using data/images/restaurant_images/"
    elif [ -d "data/images/sample_images" ]; then
        echo -e "${YELLOW}⚠${NC} Images: Using data/images/sample_images/ (limited dataset)"
    else
        mkdir -p data/images
        echo -e "${RED}✗${NC} Images: No images found - create data/images/ and add photos"
    fi
fi

echo ""
echo "Verifying final structure..."
echo "=========================================="

ls -lh data/*.{db,faiss,npy,csv} 2>/dev/null | awk '{print $9, "(" $5 ")"}'

if [ -d "data/images/restaurant_images" ]; then
    IMG_COUNT=$(ls -1 data/images/restaurant_images/ 2>/dev/null | wc -l | tr -d ' ')
    echo "data/images/restaurant_images/ ($IMG_COUNT files)"
elif [ -d "data/images/sample_images" ]; then
    IMG_COUNT=$(ls -1 data/images/sample_images/ 2>/dev/null | wc -l | tr -d ' ')
    echo "data/images/sample_images/ ($IMG_COUNT files)"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✓ Data setup complete!${NC}"
echo ""
echo "File locations:"
echo "  • Database:    data/vibecheck.db"
echo "  • FAISS Index: data/vibecheck_index.faiss"
echo "  • Metadata:    data/meta_ids.npy"
echo "  • Vibe Map:    data/vibe_map.csv"
echo "  • Images:      data/images/"
echo ""
echo "Next steps:"
echo "  1. docker-compose build"
echo "  2. docker-compose up"
echo "  3. Open http://localhost:5000"
echo "=========================================="
