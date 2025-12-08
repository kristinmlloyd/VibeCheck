Overview

This repository contains a Flask web app (`app/app.py`) and supporting code under `src/`. The app requires precomputed artifacts (SQLite DB, FAISS index, `meta_ids.npy`, and images) to run.

What this change adds

- A `render.yaml` manifest configured to deploy the Flask app using the Dockerfile at `docker/app/Dockerfile`.
- Guidance below for deploying on Render, options for storing artifacts, and local testing commands.

Quick Render deployment steps

1. Commit and push this branch (`deploy_app`) to GitHub.

2. On Render, create a new Web Service and connect your GitHub repository. Render should detect `render.yaml` and create the service configuration automatically. If it doesn't, choose Environment = Docker and set the Dockerfile path to `docker/app/Dockerfile`.

3. Provide artifact storage (choose one):
   - Attach a Render Persistent Disk and place your artifacts at the paths referenced by env vars (e.g., `/data/vibecheck.db`).
   - Configure S3 (or other object store) and use the startup script `scripts/fetch_artifacts.sh` (requires AWS creds in env vars). See below.
   - For small artifacts only: include them in the repo under `data/` (not recommended for large files).

Local build & run (fast smoke test)

Build the image locally and run it, mounting a local `data/` directory containing the required artifacts:

```bash
docker build -f docker/app/Dockerfile -t vibecheck:local .
docker run -p 8080:8080 \
  -e FLASK_PORT=8080 \
  -e DB_PATH=/data/vibecheck.db \
  -v "$(pwd)/data:/data" \
  vibecheck:local
```

Notes & recommendations

- The project depends on heavy packages (`torch`, `faiss-cpu`, `clip`) which can make cloud builds slow. Consider building the image locally and pushing to a registry (GitHub Container Registry, Docker Hub) and point Render to the image.
- If you need GPU inference, choose a GPU instance on Render (paid plan) and ensure your image uses a CUDA-enabled PyTorch wheel.
- Use a Render disk or S3 for large artifacts; do not store large binaries in git.

Optional: artifact fetch script (S3)

If you prefer to keep artifacts in S3, add these env vars to Render and the container will be able to fetch artifacts on startup:

- `S3_BUCKET`, `S3_PREFIX`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`

The repo includes `scripts/fetch_artifacts.sh` which can be used in the Dockerfile or in an entrypoint to download the necessary files.

If you'd like, I can:
- Add the startup script into the Dockerfile so artifacts are fetched at container start (requires providing S3 credentials).
- Prepare a local image build + push guide to a container registry and a `render.yaml` variant that uses a public image.
