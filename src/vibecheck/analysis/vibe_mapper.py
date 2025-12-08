# src/vibecheck/analysis/vibe_mapper.py

"""UMAP + HDBSCAN clustering for vibe map visualization."""

from pathlib import Path
from typing import Optional

import hdbscan
import mlflow
import numpy as np
import pandas as pd
import umap
from tqdm import tqdm

from vibecheck.database import RestaurantDatabase
from vibecheck.logging_config import get_logger
from vibecheck.mlflow_config import MLFlowConfig

logger = get_logger(__name__)


class VibeMapper:
    """
    Create 2D visualization of restaurant vibes using UMAP + HDBSCAN.
    """

    def __init__(
        self,
        embeddings_path: Path = Path("data/embeddings/vibe_embeddings.npy"),
        meta_ids_path: Path = Path("data/restaurants_info/meta_ids.npy"),
        db_path: Path = Path("data/restaurants_info/restaurants.db"),
        use_mlflow: bool = True,
    ):
        """Initialize mapper with embeddings and metadata."""
        logger.info("Initializing VibeMapper")

        logger.debug(f"Loading embeddings from: {embeddings_path}")
        self.embeddings = np.load(embeddings_path)
        logger.info(f"Loaded embeddings: shape={self.embeddings.shape}")

        logger.debug(f"Loading meta_ids from: {meta_ids_path}")
        self.meta_ids = np.load(meta_ids_path)
        logger.info(f"Loaded {len(self.meta_ids)} restaurant IDs")

        self.db = RestaurantDatabase(db_path)
        self.use_mlflow = use_mlflow

    def create_map(
        self,
        n_neighbors: int = 10,
        min_dist: float = 0.05,
        min_cluster_size: int = 5,
        run_name: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Create 2D vibe map with clusters.

        Args:
            n_neighbors: UMAP n_neighbors parameter.
            min_dist: UMAP min_dist parameter.
            min_cluster_size: HDBSCAN min_cluster_size parameter.
            run_name: Optional name for the MLFlow run.

        Returns:
            DataFrame with columns: id, x, y, cluster, name, rating, categories.
        """
        logger.info("Creating vibe map")
        logger.debug(f"UMAP params: n_neighbors={n_neighbors}, min_dist={min_dist}")
        logger.debug(f"HDBSCAN params: min_cluster_size={min_cluster_size}")

        # Start MLFlow run if enabled
        if self.use_mlflow:
            experiment_id = MLFlowConfig.get_or_create_experiment(
                MLFlowConfig.VIBE_MAPPING_EXPERIMENT
            )
            mlflow.start_run(experiment_id=experiment_id, run_name=run_name)

            # Log parameters
            mlflow.log_param("n_neighbors", n_neighbors)
            mlflow.log_param("min_dist", min_dist)
            mlflow.log_param("min_cluster_size", min_cluster_size)
            mlflow.log_param("umap_metric", "cosine")
            mlflow.log_param("hdbscan_metric", "euclidean")
            mlflow.log_param("hdbscan_min_samples", 2)
            mlflow.log_param("num_restaurants", len(self.embeddings))
            mlflow.log_param("embedding_dim", self.embeddings.shape[1])

        try:
            # UMAP projection
            logger.info("Running UMAP projection...")
            reducer = umap.UMAP(
                n_neighbors=n_neighbors, min_dist=min_dist, metric="cosine", random_state=42
            )
            embedding_2d = reducer.fit_transform(self.embeddings)
            logger.info("UMAP projection complete")

            # HDBSCAN clustering
            logger.info("Running HDBSCAN clustering...")
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=min_cluster_size, min_samples=2, metric="euclidean"
            )
            labels = clusterer.fit_predict(embedding_2d)
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            n_noise = np.sum(labels == -1)
            logger.info(f"Found {n_clusters} clusters")

            # Get metadata
            logger.info("Fetching restaurant metadata...")
            names, ratings, categories = [], [], []
            for rid in tqdm(self.meta_ids, desc="Fetching metadata"):
                info = self.db.get_restaurant(rid)
                if info:
                    names.append(info["name"])
                    ratings.append(info["rating"])
                    categories.append(info["categories"])
                else:
                    names.append("Unknown")
                    ratings.append(None)
                    categories.append("")

            # Create DataFrame
            df = pd.DataFrame(
                {
                    "id": self.meta_ids,
                    "x": embedding_2d[:, 0],
                    "y": embedding_2d[:, 1],
                    "cluster": labels,
                    "name": names,
                    "rating": ratings,
                    "categories": categories,
                }
            )

            logger.info(f"Vibe map created: {len(df)} points, {n_clusters} clusters")

            # Log metrics to MLFlow
            if self.use_mlflow:
                mlflow.log_metric("num_clusters", n_clusters)
                mlflow.log_metric("noise_points", n_noise)
                mlflow.log_metric("clustered_points", len(df) - n_noise)
                mlflow.log_metric("cluster_ratio", (len(df) - n_noise) / len(df) if len(df) > 0 else 0)

                # Cluster size statistics
                cluster_sizes = df[df['cluster'] != -1].groupby('cluster').size()
                if len(cluster_sizes) > 0:
                    mlflow.log_metric("avg_cluster_size", float(cluster_sizes.mean()))
                    mlflow.log_metric("max_cluster_size", int(cluster_sizes.max()))
                    mlflow.log_metric("min_cluster_size", int(cluster_sizes.min()))
                    mlflow.log_metric("cluster_size_std", float(cluster_sizes.std()))

                # Log cluster probabilities if available
                if hasattr(clusterer, 'probabilities_'):
                    mlflow.log_metric("avg_cluster_probability", float(np.mean(clusterer.probabilities_)))
                    mlflow.log_metric("min_cluster_probability", float(np.min(clusterer.probabilities_)))

                logger.info("Metrics logged to MLFlow")

        finally:
            if self.use_mlflow:
                mlflow.end_run()

        return df
