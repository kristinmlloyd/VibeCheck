# MLOps Guide: MLFlow, DVC & Evidently

Quick guide for experiment tracking, data versioning, and model monitoring in VibeCheck.

## Setup

```bash
poetry install  # Installs mlflow, dvc, evidently
```

## MLFlow - Experiment Tracking

Track parameters and metrics for embedding generation and vibe mapping.

### Quick Start

```bash
# Initialize and start UI
poetry run python scripts/init_mlflow.py
mlflow ui --port 5000

# Or use Docker (production)
docker-compose -f docker-compose.mlflow.yml up -d
```

Access at [http://localhost:5000](http://localhost:5000)

### Usage

```python
from vibecheck.embeddings import EmbeddingGenerator
from vibecheck.mlflow_config import init_mlflow

init_mlflow()
generator = EmbeddingGenerator(use_mlflow=True)
embeddings, ids = generator.generate_all(run_name="experiment_v1")
```

**Tracked Experiments:**
- `vibecheck-embeddings`: Model names, dimensions, success rate, image coverage
- `vibecheck-vibe-mapping`: UMAP/HDBSCAN params, cluster count, cluster statistics

## DVC - Data Version Control

Track large files (images, embeddings) and create reproducible pipelines.

### Track Data

```bash
dvc add data/images/sample_images
dvc add data/embeddings/vibe_embeddings.npy
git add data/**/*.dvc .dvc/
git commit -m "Track data with DVC"

# Configure remote storage (optional)
dvc remote add -d s3remote s3://my-bucket/dvc-storage
dvc push
```

### Run Pipeline

Pipeline defined in `dvc.yaml`, parameters in `params.yaml`.

```bash
dvc repro         # Run full pipeline
dvc dag           # View pipeline structure
dvc metrics show  # Show metrics
dvc metrics diff  # Compare with previous run
```

### Experiment with Parameters

```bash
vim params.yaml   # Edit parameters
dvc repro         # Rerun pipeline
dvc metrics diff  # Compare results
```

## Evidently - Model Monitoring

Monitor embedding drift, data quality, and recommendation performance.

### Generate Reports

```bash
poetry run python scripts/generate_monitoring_report.py
# Reports saved to monitoring/reports/
```

### Usage in Code

```python
from vibecheck.monitoring import EvidentlyMonitor

monitor = EvidentlyMonitor()
report_path = monitor.create_embedding_drift_report(
    reference_embeddings=baseline_embeddings,
    current_embeddings=new_embeddings,
    reference_ids=baseline_ids,
    current_ids=new_ids
)
```

## Complete Workflow

```bash
# 1. Start MLFlow
poetry run python scripts/init_mlflow.py
mlflow ui --port 5000 &

# 2. Run pipeline with tracking
dvc repro

# 3. Track results with DVC
dvc add data/embeddings/*.npy
git add data/**/*.dvc
git commit -m "Update embeddings"
dvc push

# 4. Generate monitoring reports
poetry run python scripts/generate_monitoring_report.py

# 5. View results
# - MLFlow UI: http://localhost:5000
# - Evidently: open monitoring/reports/*.html
```

## Configuration Files

- `mlflow.ini` - MLFlow server config
- `docker-compose.mlflow.yml` - Docker setup
- `dvc.yaml` - Pipeline definition
- `params.yaml` - Pipeline parameters
- `.dvc/config` - DVC remote storage

## Troubleshooting

**MLFlow not connecting:**
```bash
python -c "import mlflow; print(mlflow.get_tracking_uri())"
# Should show: http://localhost:5000
```

**DVC remote issues:**
```bash
dvc remote list
dvc status
```

**Monitoring reports fail:**
```bash
# Ensure embeddings exist
ls -lh data/embeddings/
poetry run python scripts/generate_embeddings.py
```
