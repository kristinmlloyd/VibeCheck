# src/vibecheck/embeddings/generator.py
"""Generate embeddings for restaurants."""

from pathlib import Path

import numpy as np
import torch
from PIL import Image
from tqdm import tqdm

from vibecheck.database import RestaurantDatabase
from vibecheck.embeddings.models import ModelCache


class EmbeddingGenerator:
    """
    Generate embeddings for restaurant text and images.

    Example:
        >>> generator = EmbeddingGenerator()
        >>> embeddings, ids = generator.generate_all()
        >>> print(f"Generated {len(embeddings)} embeddings")
    """

    def __init__(
        self,
        db_path: Path = Path("data/raw/restaurants.db"),
        image_dir: Path = Path("data/images/sample_images"),
    ):
        """Initialize generator with database and image directory."""
        self.db = RestaurantDatabase(db_path)
        self.image_dir = Path(image_dir)

        # Load models
        self.text_model = ModelCache.get_text_model()
        self.clip_model, self.clip_preprocess = ModelCache.get_clip_model()
        self.device = ModelCache.get_device()

    def generate_text_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text."""
        return self.text_model.encode(
            text, convert_to_numpy=True, normalize_embeddings=True
        )

    def generate_image_embedding(self, image_path: Path) -> np.ndarray:
        """Generate CLIP embedding for image."""
        try:
            image = (
                self.clip_preprocess(Image.open(image_path))
                .unsqueeze(0)
                .to(self.device)
            )

            with torch.no_grad():
                img_vec = self.clip_model.encode_image(image)

            img_vec /= img_vec.norm(dim=-1, keepdim=True)
            return img_vec.cpu().numpy()[0]

        except Exception as e:
            print(f"Error processing image {image_path}: {e}")
            return np.zeros((512,))

    def generate_restaurant_embedding(
        self, restaurant_id: str, text: str
    ) -> np.ndarray:
        """
        Generate combined embedding for a restaurant.

        Args:
            restaurant_id: Restaurant ID for finding image.
            text: Text to embed (review snippet or name).

        Returns:
            Combined embedding vector (384 text + 512 image = 896 dims).
        """
        # Text embedding
        text_vec = self.generate_text_embedding(text or "")

        # Image embedding
        img_path = self.image_dir / f"{restaurant_id}.jpg"
        if img_path.exists():
            img_vec = self.generate_image_embedding(img_path)
        else:
            img_vec = np.zeros((512,))

        # Combine
        return np.concatenate([text_vec, img_vec]).astype("float32")

    def generate_all(self) -> tuple[np.ndarray, list[str]]:
        """
        Generate embeddings for all restaurants in database.

        Returns:
            Tuple of (embeddings array, list of restaurant IDs).
        """
        restaurants = self.db.get_all_restaurants()

        embeddings = []
        meta_ids = []

        for resto in tqdm(restaurants, desc="Generating embeddings"):
            text = resto["review_snippet"] or resto["name"] or ""
            embedding = self.generate_restaurant_embedding(resto["id"], text)

            embeddings.append(embedding)
            meta_ids.append(resto["id"])

        return np.vstack(embeddings).astype("float32"), meta_ids
