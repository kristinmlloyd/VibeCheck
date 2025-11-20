# src/vibecheck/recommender.py

"""Core recommendation engine for VibeCheck."""

import sqlite3  # Add this import
from pathlib import Path
from typing import Any  # Add Tuple here

import faiss
import numpy as np
import torch
from PIL import Image

from vibecheck.database import RestaurantDatabase
from vibecheck.embeddings.models import ModelCache


class VibeCheckRecommender:
    """Main recommendation engine - same as before but with updated paths."""

    def __init__(
        self,
        db_path: Path = Path("data/raw/restaurants.db"),
        image_dir: Path = Path("data/images/sample_images"),
        faiss_index_path: Path = Path("data/processed/vibecheck_index.faiss"),
        meta_ids_path: Path = Path("data/processed/meta_ids.npy"),
    ):
        """Initialize with new data paths."""
        self.db = RestaurantDatabase(db_path)
        self.image_dir = Path(image_dir)

        # Load models
        self.text_model = ModelCache.get_text_model()
        self.clip_model, self.clip_preprocess = ModelCache.get_clip_model()
        self.device = ModelCache.get_device()

        # Load search index
        self.index = faiss.read_index(str(faiss_index_path))
        self.meta_ids = np.load(str(meta_ids_path))

    def encode_text(self, text: str) -> np.ndarray:
        """
        Encode text query into embedding vector.

        Args:
            text: Text description of desired vibe.

        Returns:
            Normalized embedding vector of shape (384,).

        Example:
            >>> recommender = VibeCheckRecommender()
            >>> vector = recommender.encode_text("cozy cafe")
            >>> vector.shape
            (384,)
        """
        return self.text_model.encode(
            text, convert_to_numpy=True, normalize_embeddings=True
        )

    def encode_image(self, image: Image.Image) -> np.ndarray:
        """
        Encode image into CLIP embedding vector.

        Args:
            image: PIL Image of desired aesthetic.

        Returns:
            Normalized embedding vector of shape (512,).

        Example:
            >>> from PIL import Image
            >>> recommender = VibeCheckRecommender()
            >>> img = Image.open("restaurant.jpg")
            >>> vector = recommender.encode_image(img)
            >>> vector.shape
            (512,)
        """
        img_tensor = self.clip_preprocess(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            img_vec = self.clip_model.encode_image(img_tensor)

        img_vec /= img_vec.norm(dim=-1, keepdim=True)
        return img_vec.cpu().numpy()[0]

    def encode_query(
        self, text: str | None = None, image: Image.Image | None = None
    ) -> np.ndarray:
        """
        Encode a multimodal query (text and/or image) into a combined embedding.

        Args:
            text: Optional text description of desired vibe.
            image: Optional PIL Image of desired aesthetic.

        Returns:
            Combined embedding vector of shape (896,) = (384 text + 512 image).

        Raises:
            ValueError: If both text and image are None.

        Example:
            >>> recommender = VibeCheckRecommender()
            >>> # Text only
            >>> vec = recommender.encode_query(text="cozy cafe")
            >>> # Image only
            >>> from PIL import Image
            >>> img = Image.open("cafe.jpg")
            >>> vec = recommender.encode_query(image=img)
            >>> # Both
            >>> vec = recommender.encode_query(text="cozy cafe", image=img)
        """
        if text is None and image is None:
            raise ValueError("Must provide either text or image query")

        # Encode text (or use zeros if not provided)
        text_vec = self.encode_text(text) if text else np.zeros((384,))

        # Encode image (or use zeros if not provided)
        image_vec = self.encode_image(image) if image else np.zeros((512,))

        # Concatenate into single vector
        combined = np.concatenate([text_vec, image_vec]).astype("float32")
        return combined[None, :]  # Add batch dimension

    def search(
        self, query_vector: np.ndarray, top_k: int = 5
    ) -> list[tuple[str, float]]:
        """
        Search the FAISS index for similar restaurants.

        Args:
            query_vector: Query embedding vector of shape (1, 896).
            top_k: Number of top results to return.

        Returns:
            List of (restaurant_id, distance) tuples.

        Example:
            >>> recommender = VibeCheckRecommender()
            >>> query_vec = recommender.encode_query(text="cozy cafe")
            >>> results = recommender.search(query_vec, top_k=5)
            >>> for rid, distance in results:
            ...     print(f"Restaurant {rid}: distance={distance:.4f}")
        """
        distances, indices = self.index.search(query_vector, top_k)

        results = []
        for idx, distance in zip(indices[0], distances[0], strict=False):
            restaurant_id = self.meta_ids[idx]
            results.append((restaurant_id, float(distance)))

        return results

    def get_restaurant_info(self, restaurant_id: str) -> dict[str, Any] | None:
        """
        Get detailed information about a restaurant from the database.

        Args:
            restaurant_id: Unique restaurant identifier.

        Returns:
            Dictionary with restaurant details or None if not found.
            Keys: 'id', 'name', 'rating', 'address', 'image_url', 'image_path'

        Example:
            >>> recommender = VibeCheckRecommender()
            >>> info = recommender.get_restaurant_info("some_id")
            >>> print(info['name'])
            >>> print(info['rating'])
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute(
                    "SELECT name, rating, address, image_url FROM restaurants WHERE id=?",
                    (restaurant_id,),
                ).fetchone()

            if not row:
                return None

            name, rating, address, image_url = row
            image_path = self.image_dir / f"{restaurant_id}.jpg"

            return {
                "id": restaurant_id,
                "name": name,
                "rating": rating,
                "address": address,
                "image_url": image_url,
                "image_path": str(image_path) if image_path.exists() else None,
            }

        except Exception as e:
            print(f"Error fetching restaurant {restaurant_id}: {e}")
            return None

    def search_by_text(self, text: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Search for restaurants matching a text description.

        Args:
            text: Description of desired vibe (e.g., "cozy cafe with plants").
            top_k: Number of results to return.

        Returns:
            List of restaurant dictionaries with full information.

        Example:
            >>> recommender = VibeCheckRecommender()
            >>> results = recommender.search_by_text("cozy cafe with plants", top_k=3)
            >>> for resto in results:
            ...     print(f"{resto['name']}: {resto['rating']} stars")
        """
        query_vec = self.encode_query(text=text)
        search_results = self.search(query_vec, top_k=top_k)

        restaurants = []
        for restaurant_id, distance in search_results:
            info = self.get_restaurant_info(restaurant_id)
            if info:
                info["distance"] = distance
                info["similarity"] = 1.0 / (
                    1.0 + distance
                )  # Convert distance to similarity
                restaurants.append(info)

        return restaurants

    def search_by_image(
        self, image: Image.Image, top_k: int = 5
    ) -> list[dict[str, Any]]:
        """
        Search for restaurants matching an image aesthetic.

        Args:
            image: PIL Image of desired aesthetic.
            top_k: Number of results to return.

        Returns:
            List of restaurant dictionaries with full information.

        Example:
            >>> from PIL import Image
            >>> recommender = VibeCheckRecommender()
            >>> img = Image.open("ideal_restaurant.jpg")
            >>> results = recommender.search_by_image(img, top_k=3)
            >>> for resto in results:
            ...     print(resto['name'])
        """
        query_vec = self.encode_query(image=image)
        search_results = self.search(query_vec, top_k=top_k)

        restaurants = []
        for restaurant_id, distance in search_results:
            info = self.get_restaurant_info(restaurant_id)
            if info:
                info["distance"] = distance
                info["similarity"] = 1.0 / (1.0 + distance)
                restaurants.append(info)

        return restaurants

    def search_multimodal(
        self, text: str | None = None, image: Image.Image | None = None, top_k: int = 5
    ) -> list[dict[str, Any]]:
        """
        Search using both text and image simultaneously.

        Args:
            text: Optional text description.
            image: Optional PIL Image.
            top_k: Number of results to return.

        Returns:
            List of restaurant dictionaries with full information.

        Example:
            >>> from PIL import Image
            >>> recommender = VibeCheckRecommender()
            >>> img = Image.open("cafe.jpg")
            >>> results = recommender.search_multimodal(
            ...     text="cozy atmosphere",
            ...     image=img,
            ...     top_k=5
            ... )
        """
        query_vec = self.encode_query(text=text, image=image)
        search_results = self.search(query_vec, top_k=top_k)

        restaurants = []
        for restaurant_id, distance in search_results:
            info = self.get_restaurant_info(restaurant_id)
            if info:
                info["distance"] = distance
                info["similarity"] = 1.0 / (1.0 + distance)
                restaurants.append(info)

        return restaurants
