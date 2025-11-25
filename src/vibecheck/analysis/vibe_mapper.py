# src/vibecheck/analysis/vibe_mapper.py

"""UMAP + HDBSCAN clustering for vibe map visualization."""

from pathlib import Path

import hdbscan
import numpy as np
import pandas as pd
import umap
from tqdm import tqdm

from vibecheck.database import RestaurantDatabase
from vibecheck.logging_config import get_logger

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

    def create_map(
        self, n_neighbors: int = 10, min_dist: float = 0.05, min_cluster_size: int = 5
    ) -> pd.DataFrame:
        """
        Create 2D vibe map with clusters.

        Args:
            n_neighbors: UMAP n_neighbors parameter.
            min_dist: UMAP min_dist parameter.
            min_cluster_size: HDBSCAN min_cluster_size parameter.

        Returns:
            DataFrame with columns: id, x, y, cluster, name, rating, categories.
        """
        logger.info("Creating vibe map")
        logger.debug(f"UMAP params: n_neighbors={n_neighbors}, min_dist={min_dist}")
        logger.debug(f"HDBSCAN params: min_cluster_size={min_cluster_size}")

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
        return df
