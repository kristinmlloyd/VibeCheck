#!/bin/bash
# Download data files from Google Drive on startup

set -e

DATA_DIR="${OUTPUT_DIR:-/app/data}"

echo "Creating data directory..."
mkdir -p "$DATA_DIR"

# Function to download from Google Drive
download_gdrive() {
    local file_id=$1
    local output_path=$2
    echo "Downloading $output_path..."
    
    # Use gdown to download from Google Drive
    pip install --no-cache-dir gdown
    gdown "https://drive.google.com/uc?id=${file_id}" -O "$output_path" || echo "Failed to download $output_path"
}

# Download data files from Google Drive folders

# Download images folder
echo "Downloading images folder..."
pip install --no-cache-dir gdown
gdown --folder "https://drive.google.com/drive/folders/1xsBiDjT3b_EmUDLsSh5p84vPp_nVpZ6g" -O "$DATA_DIR/images" --remaining-ok || echo "Warning: Some images may have failed to download"

# Download output data files folder (contains db, faiss, etc.)
echo "Downloading data files..."
mkdir -p "$DATA_DIR/temp_output"
gdown --folder "https://drive.google.com/drive/folders/1TSRpIwOkLwXAZCkpY2VDBPoAtYbHw3zS" -O "$DATA_DIR/temp_output" --remaining-ok || echo "Warning: Some data files may have failed to download"

# Move files from temp_output to data directory
if [ -d "$DATA_DIR/temp_output" ]; then
    mv "$DATA_DIR/temp_output"/* "$DATA_DIR/" 2>/dev/null || true
    rm -rf "$DATA_DIR/temp_output"
fi

echo "Data download complete!"
ls -lh "$DATA_DIR"
