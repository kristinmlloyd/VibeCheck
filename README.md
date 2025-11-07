---
title: VibeCheck
emoji: 🍽️
colorFrom: blue
colorTo: purple
sdk: streamlit
sdk_version: "1.28.0"
app_file: vibecheck_app.py
pinned: false
---
hi
# VibeCheck

VibeCheck helps users discover restaurants by ambience rather than cuisine or ratings. It uses multimodal embeddings (text + image) to match user-input descriptions or photos with restaurants that share similar aesthetic and contextual features.

## Features
- Search by image upload
- Search by text description
- Multimodal embeddings (CLIP + Sentence-BERT)
- FAISS-powered similarity search
- Visual clustering with UMAP + HDBSCAN
