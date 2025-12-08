# src/vibecheck/recommender.py

# src/vibecheck/recommender.py

"""Core recommendation engine for VibeCheck."""

import sqlite3
from pathlib import Path
from typing import Any

import faiss
import numpy as np
import torch
from PIL import Image

from vibecheck.database import RestaurantDatabase
from vibecheck.embeddings.models import ModelCache
from vibecheck.logging_config import get_logger

logger = get_logger(__name__)


class VibeCheckRecommender:
    """Main recommendation engine - same as before but with updated paths."""

    def __init__(
        self,
        db_path: Path = Path("data/restaurants_info/restaurants.db"),
        image_dir: Path = Path("data/images/sample_images"),
        faiss_index_path: Path = Path("data/embeddings/vibecheck_index.faiss"),
        meta_ids_path: Path = Path("data/restaurants_info/meta_ids.npy"),
    ):
        """Initialize with new data paths."""
        logger.info("Initializing VibeCheckRecommender")
        logger.debug(f"Database path: {db_path}")
        logger.debug(f"Image directory: {image_dir}")
        logger.debug(f"FAISS index: {faiss_index_path}")
        logger.debug(f"Meta IDs: {meta_ids_path}")

        self.db = RestaurantDatabase(db_path)
        self.db_path = db_path  # Store for get_restaurant_info
        self.image_dir = Path(image_dir)

        # Load models
        logger.info("Loading models...")
        self.text_model = ModelCache.get_text_model()
        self.clip_model, self.clip_preprocess = ModelCache.get_clip_model()
        self.device = ModelCache.get_device()

        # Load search index
        logger.info("Loading FAISS index...")
        try:
            self.index = faiss.read_index(str(faiss_index_path))
            self.meta_ids = np.load(str(meta_ids_path))
            logger.info(f"Loaded index with {len(self.meta_ids)} entries")
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            raise

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
        logger.debug(
            f"Encoding text: {text[:50]}..."
            if len(text) > 50
            else f"Encoding text: {text}"
        )
        embedding: np.ndarray = self.text_model.encode(
            text, convert_to_numpy=True, normalize_embeddings=True
        )
        return embedding

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
        logger.debug("Encoding image...")
        img_tensor = self.clip_preprocess(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            img_vec = self.clip_model.encode_image(img_tensor)

        img_vec /= img_vec.norm(dim=-1, keepdim=True)
        result: np.ndarray = img_vec.cpu().numpy()[0]
        return result

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
            logger.error("encode_query called with no text or image")
            raise ValueError("Must provide either text or image query")

        logger.info(f"Encoding query - text: {bool(text)}, image: {bool(image)}")

        # Encode text (or use zeros if not provided)
        text_vec = self.encode_text(text) if text else np.zeros((384,))

        # Encode image (or use zeros if not provided)
        image_vec = self.encode_image(image) if image else np.zeros((512,))

        # Concatenate into single vector
        combined = np.concatenate([text_vec, image_vec]).astype("float32")
        result: np.ndarray = combined[None, :]  # Add batch dimension
        return result

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
        logger.debug(f"Searching index for top {top_k} results")
        distances, indices = self.index.search(query_vector, top_k)

        results = []
        for idx, distance in zip(indices[0], distances[0], strict=False):
            restaurant_id = self.meta_ids[idx]
            results.append((restaurant_id, float(distance)))

        logger.debug(f"Found {len(results)} results")
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
        logger.debug(f"Fetching restaurant info: {restaurant_id}")
        try:
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute(
                    "SELECT name, rating, address, image_url FROM restaurants WHERE id=?",
                    (restaurant_id,),
                ).fetchone()

            if not row:
                logger.debug(f"Restaurant not found: {restaurant_id}")
                return None

            name, rating, address, image_url = row
            image_path = self.image_dir / f"{restaurant_id}.jpg"

            logger.debug(f"Found restaurant: {name}")
            return {
                "id": restaurant_id,
                "name": name,
                "rating": rating,
                "address": address,
                "image_url": image_url,
                "image_path": str(image_path) if image_path.exists() else None,
            }

        except Exception as e:
            logger.error(f"Error fetching restaurant {restaurant_id}: {e}")
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
        logger.info(
            f"Text search: '{text[:50]}...' (top_k={top_k})"
            if len(text) > 50
            else f"Text search: '{text}' (top_k={top_k})"
        )

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

        logger.info(f"Returning {len(restaurants)} results")
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
        logger.info(f"Image search (top_k={top_k})")

        query_vec = self.encode_query(image=image)
        search_results = self.search(query_vec, top_k=top_k)

        restaurants = []
        for restaurant_id, distance in search_results:
            info = self.get_restaurant_info(restaurant_id)
            if info:
                info["distance"] = distance
                info["similarity"] = 1.0 / (1.0 + distance)
                restaurants.append(info)

        logger.info(f"Returning {len(restaurants)} results")
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
        logger.info(
            f"Multimodal search (text={bool(text)}, image={bool(image)}, top_k={top_k})"
        )

        query_vec = self.encode_query(text=text, image=image)
        search_results = self.search(query_vec, top_k=top_k)

        restaurants = []
        for restaurant_id, distance in search_results:
            info = self.get_restaurant_info(restaurant_id)
            if info:
                info["distance"] = distance
                info["similarity"] = 1.0 / (1.0 + distance)
                restaurants.append(info)

        logger.info(f"Returning {len(restaurants)} results")
        return restaurants
