#!/bin/bash

# VibeCheck - Hugging Face Spaces Deployment Script
# This script helps prepare files for deployment to Hugging Face Spaces

set -e  # Exit on error

echo "=========================================="
echo "VibeCheck - Hugging Face Deployment Prep"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if HF username is provided
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: ./deploy_to_hf.sh YOUR_HF_USERNAME SPACE_NAME${NC}"
    echo ""
    echo "Example: ./deploy_to_hf.sh johndoe vibecheck"
    echo ""
    echo "This will create a directory ready to push to:"
    echo "https://huggingface.co/spaces/johndoe/vibecheck"
    exit 1
fi

HF_USERNAME=$1
SPACE_NAME=${2:-vibecheck}
DEPLOY_DIR="hf_space_${SPACE_NAME}"

echo "Configuration:"
echo "  Username: $HF_USERNAME"
echo "  Space Name: $SPACE_NAME"
echo "  Deploy Directory: $DEPLOY_DIR"
echo ""

# Step 1: Create deployment directory
echo -e "${GREEN}[1/7] Creating deployment directory...${NC}"
if [ -d "$DEPLOY_DIR" ]; then
    echo -e "${YELLOW}Warning: Directory $DEPLOY_DIR already exists. Remove it? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        rm -rf "$DEPLOY_DIR"
    else
        echo "Exiting..."
        exit 1
    fi
fi
mkdir -p "$DEPLOY_DIR"
echo "✓ Created $DEPLOY_DIR"

# Step 2: Clone HF Space
echo ""
echo -e "${GREEN}[2/7] Cloning Hugging Face Space...${NC}"
echo "Make sure you've created the Space at:"
echo "https://huggingface.co/spaces/$HF_USERNAME/$SPACE_NAME"
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read -r

cd "$DEPLOY_DIR"
git lfs install
git clone "https://huggingface.co/spaces/$HF_USERNAME/$SPACE_NAME" .
cd ..
echo "✓ Cloned Space repository"

# Step 3: Copy application files
echo ""
echo -e "${GREEN}[3/7] Copying application files...${NC}"

# Copy Gradio app as app.py
cp app_gradio.py "$DEPLOY_DIR/app.py"
echo "✓ Copied app_gradio.py → app.py"

# Copy requirements
cp requirements_hf.txt "$DEPLOY_DIR/requirements.txt"
echo "✓ Copied requirements_hf.txt → requirements.txt"

# Copy gitattributes for LFS
cp .gitattributes_hf "$DEPLOY_DIR/.gitattributes"
echo "✓ Copied .gitattributes_hf → .gitattributes"

# Step 4: Create README
echo ""
echo -e "${GREEN}[4/7] Creating README.md...${NC}"
cat > "$DEPLOY_DIR/README.md" << 'EOF'
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

Find restaurants based on their **vibe and atmosphere** using AI-powered multimodal search!

## 🌟 Features

- 📝 **Text Search**: Describe the ambience you're looking for
- 🖼️ **Image Search**: Upload a reference photo
- 🔄 **Hybrid Search**: Combine text and image for precise results
- 🤖 **Powered by**: CLIP, Sentence-BERT, and FAISS

## 🚀 How to Use

1. Enter a text description of your ideal restaurant vibe
2. Or upload a reference image of a restaurant atmosphere
3. Or combine both for more accurate results!
4. Browse the top matching restaurants with images and details

## 💡 Example Queries

- "cozy romantic lighting with rustic wooden furniture"
- "bright modern cafe with minimalist design"
- "upscale fine dining with elegant chandeliers"
- "casual outdoor patio with string lights"

## 🛠️ Technology

- **CLIP** (OpenAI): Multimodal image-text understanding
- **Sentence-BERT**: Advanced text embeddings
- **FAISS**: Efficient similarity search
- **Gradio**: Interactive web interface

## 📚 More Information

- [GitHub Repository](https://github.com/manav-ar/VibeCheck)
- [Documentation](https://github.com/manav-ar/VibeCheck/blob/main/README.md)

---

Built with ❤️ by the VibeCheck team
EOF
echo "✓ Created README.md"

# Step 5: Setup Git LFS
echo ""
echo -e "${GREEN}[5/7] Setting up Git LFS for large files...${NC}"
cd "$DEPLOY_DIR"
git lfs track "*.faiss"
git lfs track "*.npy"
git lfs track "*.db"
git lfs track "data/images/*"
git add .gitattributes
cd ..
echo "✓ Configured Git LFS"

# Step 6: Copy data files
echo ""
echo -e "${GREEN}[6/7] Preparing data directory...${NC}"
mkdir -p "$DEPLOY_DIR/data"
echo "✓ Created data directory"
echo ""
echo -e "${YELLOW}IMPORTANT: You need to copy your data files manually:${NC}"
echo ""
echo "Copy these files to $DEPLOY_DIR/data/:"
echo "  1. vibecheck.db"
echo "  2. vibecheck_index.faiss"
echo "  3. meta_ids.npy"
echo "  4. images/ directory (all restaurant images)"
echo ""
echo "Example commands:"
echo "  cp /path/to/vibecheck_full_output/vibecheck.db $DEPLOY_DIR/data/"
echo "  cp /path/to/vibecheck_full_output/vibecheck_index.faiss $DEPLOY_DIR/data/"
echo "  cp /path/to/vibecheck_full_output/meta_ids.npy $DEPLOY_DIR/data/"
echo "  cp -r /path/to/vibecheck_full_output/images $DEPLOY_DIR/data/"
echo ""
echo "Or use the data from your scripts/vibecheck_full_output/ directory"
echo ""
echo "Press Enter when you've copied the files..."
read -r

# Step 7: Instructions for pushing
echo ""
echo -e "${GREEN}[7/7] Final steps...${NC}"
echo ""
echo -e "${GREEN}✓ Deployment preparation complete!${NC}"
echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo ""
echo "1. Verify data files are in place:"
echo "   cd $DEPLOY_DIR"
echo "   ls -lh data/"
echo ""
echo "2. Add and commit all files:"
echo "   git add ."
echo "   git commit -m 'Initial deployment'"
echo ""
echo "3. Push to Hugging Face:"
echo "   git push"
echo ""
echo "4. Visit your Space:"
echo "   https://huggingface.co/spaces/$HF_USERNAME/$SPACE_NAME"
echo ""
echo "5. Wait for build (5-15 minutes first time)"
echo ""
echo "=========================================="
echo ""
echo -e "${YELLOW}Troubleshooting:${NC}"
echo "- If build fails: Check 'Build logs' on your Space page"
echo "- Out of memory: Upgrade hardware in Space settings"
echo "- Files too large: Ensure Git LFS is working (git lfs ls-files)"
echo ""
echo "For detailed instructions, see: HUGGINGFACE_DEPLOYMENT.md"
echo ""
echo -e "${GREEN}Happy deploying! 🚀${NC}"
