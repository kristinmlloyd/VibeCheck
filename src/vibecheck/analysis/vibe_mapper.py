# src/vibecheck/analysis/vibe_mapper.py

"""UMAP + HDBSCAN clustering for vibe map visualization."""

from pathlib import Path

import hdbscan
import numpy as np
import pandas as pd
import umap
from tqdm import tqdm

from vibecheck.database import RestaurantDatabase


class VibeMapper:
    """
    Create 2D visualization of restaurant vibes using UMAP + HDBSCAN.

    Example:
        >>> mapper = VibeMapper()
        >>> df = mapper.create_map()
        >>> df.to_csv("data/processed/vibe_map.csv")
    """

    def __init__(
        self,
        embeddings_path: Path = Path("data/embeddings/vibe_embeddings.npy"),  # Updated
        meta_ids_path: Path = Path("data/restaurants_info/meta_ids.npy"),  # Updated
        db_path: Path = Path("data/restaurants_info/restaurants.db"),  # Updated
    ):
        """Initialize mapper with embeddings and metadata."""
        self.embeddings = np.load(embeddings_path)
        self.meta_ids = np.load(meta_ids_path)
        self.db = RestaurantDatabase(db_path)

    def create_map(self) -> pd.DataFrame:
        """
        Create 2D vibe map with clusters.

        Returns:
            DataFrame with columns: id, x, y, cluster, name, rating, categories.
        """
        print("Running UMAP projection...")
        reducer = umap.UMAP(
            n_neighbors=10, min_dist=0.05, metric="cosine", random_state=42
        )
        embedding_2d = reducer.fit_transform(self.embeddings)

        print("Clustering with HDBSCAN...")
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=5, min_samples=2, metric="euclidean"
        )
        labels = clusterer.fit_predict(embedding_2d)

        # Get metadata
        print("Fetching restaurant metadata...")
        names, ratings, categories = [], [], []
        for rid in tqdm(self.meta_ids):
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

        return df
