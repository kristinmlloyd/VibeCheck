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

# VibeCheck

VibeCheck helps users discover restaurants by ambience rather than cuisine or ratings. It uses multimodal embeddings (text + image) to match user-input descriptions or photos with restaurants that share similar aesthetic and contextual features.

## Features
- Search by image upload
- Search by text description
- Multimodal embeddings (CLIP + Sentence-BERT)
- FAISS-powered similarity search
- Visual clustering with UMAP + HDBSCAN

## Running the Application

### Quick Start
```bash
poetry run vibecheck-app
```

**Note for Mac users:** The environment variables prevent segmentation faults with CLIP/torch. Therefore, instead of running the streamlit app directly (app/streamlit_app.py), we have created a script (scripts/run_streamlit.py) that sets these variables before launching the app. Use the command above to run the app with the necessary environment variables.
