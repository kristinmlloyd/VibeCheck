#!/bin/bash

# VibeCheck Render Deployment Preparation Script
# This script helps prepare your app for Render deployment

set -e

echo "========================================"
echo "VibeCheck Render Deployment Prep"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -f "app/app.py" ]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

echo "✓ Found app/app.py"

# Option 1: Use existing Docker setup with Poetry
echo ""
echo "Choose Dockerfile option:"
echo "1) Use simplified Dockerfile (Dockerfile.render - recommended)"
echo "2) Use existing Poetry-based Dockerfile (docker/app/Dockerfile)"
read -p "Enter choice (1 or 2): " docker_choice

if [ "$docker_choice" = "1" ]; then
    echo ""
    echo "Copying Dockerfile.render to Dockerfile..."
    cp Dockerfile.render Dockerfile
    echo "✓ Dockerfile ready at project root"
elif [ "$docker_choice" = "2" ]; then
    echo ""
    echo "Copying docker/app/Dockerfile to project root..."
    cp docker/app/Dockerfile Dockerfile
    echo "✓ Dockerfile ready at project root"
    echo ""
    echo "⚠️  Note: You'll need pyproject.toml and poetry.lock in the root"
    if [ ! -f "pyproject.toml" ]; then
        echo "   Missing pyproject.toml - deployment may fail"
    fi
else
    echo "Invalid choice. Exiting."
    exit 1
fi

# Check if render.yaml exists
echo ""
if [ -f "render.yaml" ]; then
    echo "✓ Found render.yaml configuration"
else
    echo "⚠️  render.yaml not found - you'll need to configure manually in Render dashboard"
fi

# Check requirements.txt
echo ""
if [ -f "requirements.txt" ]; then
    echo "✓ Found requirements.txt"

    # Check for critical dependencies
    if grep -q "flask" requirements.txt && \
       grep -q "gunicorn" requirements.txt && \
       grep -q "faiss-cpu" requirements.txt; then
        echo "✓ All critical dependencies present"
    else
        echo "⚠️  Warning: Some dependencies might be missing"
    fi
else
    echo "❌ requirements.txt not found - required for deployment"
    exit 1
fi

# Check data directory
echo ""
echo "Checking data files..."
data_files=(
    "data/vibecheck.db"
    "data/vibecheck_index.faiss"
    "data/meta_ids.npy"
    "data/vibe_map.csv"
)

missing_files=()
for file in "${data_files[@]}"; do
    if [ -f "$file" ]; then
        size=$(du -h "$file" | cut -f1)
        echo "✓ Found $file ($size)"
    else
        echo "❌ Missing $file"
        missing_files+=("$file")
    fi
done

if [ -d "data/images" ]; then
    image_count=$(find data/images -type f | wc -l)
    echo "✓ Found data/images with $image_count files"
else
    echo "❌ Missing data/images directory"
    missing_files+=("data/images")
fi

# Calculate total data size
if [ -d "data" ]; then
    total_size=$(du -sh data | cut -f1)
    echo ""
    echo "Total data directory size: $total_size"
fi

# Git status
echo ""
echo "Checking git status..."
if git rev-parse --git-dir > /dev/null 2>&1; then
    echo "✓ Git repository detected"

    # Check if there are uncommitted changes
    if [ -n "$(git status --porcelain)" ]; then
        echo "⚠️  You have uncommitted changes"
        echo ""
        read -p "Would you like to commit changes now? (y/n): " commit_choice

        if [ "$commit_choice" = "y" ]; then
            git add Dockerfile render.yaml 2>/dev/null || true
            git status --short
            echo ""
            read -p "Enter commit message: " commit_msg
            git commit -m "$commit_msg"
            echo "✓ Changes committed"
        fi
    else
        echo "✓ No uncommitted changes"
    fi

    # Check remote
    if git remote -v | grep -q "origin"; then
        remote_url=$(git remote get-url origin)
        echo "✓ Git remote configured: $remote_url"
    else
        echo "⚠️  No git remote configured - you'll need to push to GitHub"
    fi
else
    echo "❌ Not a git repository - Render requires git integration"
    exit 1
fi

# Summary
echo ""
echo "========================================"
echo "Preparation Summary"
echo "========================================"
echo ""

if [ ${#missing_files[@]} -eq 0 ]; then
    echo "✅ All data files present"
else
    echo "⚠️  Missing ${#missing_files[@]} data file(s):"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
    echo ""
    echo "   You'll need to upload these to Render's persistent disk"
fi

echo ""
echo "Next steps:"
echo ""
echo "1. Push to GitHub:"
echo "   git push origin main"
echo ""
echo "2. Go to https://render.com and create a new Web Service"
echo ""
echo "3. Connect your GitHub repository"
echo ""
if [ -f "render.yaml" ]; then
    echo "4. Render will auto-detect render.yaml and configure everything"
else
    echo "4. Manually configure:"
    echo "   - Runtime: Docker"
    echo "   - Instance Type: Standard (2GB minimum)"
    echo "   - Add persistent disk at /app/data (10GB)"
fi
echo ""
echo "5. Upload data files to persistent disk via Render Shell"
echo ""
echo "6. Deploy!"
echo ""
echo "For detailed instructions, see RENDER_DEPLOYMENT.md"
echo ""
