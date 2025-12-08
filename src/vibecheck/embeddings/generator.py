# src/vibecheck/embeddings/generator.py
"""Generate embeddings for restaurants."""

from pathlib import Path
from typing import Optional

import mlflow
import numpy as np
import torch
from PIL import Image
from tqdm import tqdm

from vibecheck.database import RestaurantDatabase
from vibecheck.embeddings.models import ModelCache
from vibecheck.logging_config import get_logger
from vibecheck.mlflow_config import MLFlowConfig

logger = get_logger(__name__)


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
        db_path: Path = Path("data/restaurants_info/restaurants.db"),
        image_dir: Path = Path("data/images/sample_images"),
        use_mlflow: bool = True,
    ):
        """Initialize generator with database and image directory."""
        logger.info("Initializing EmbeddingGenerator")

        self.db = RestaurantDatabase(db_path)
        self.image_dir = Path(image_dir)
        self.use_mlflow = use_mlflow

        logger.debug(f"Database path: {db_path}")
        logger.debug(f"Image directory: {self.image_dir}")

        if not self.image_dir.exists():
            logger.warning(f"Image directory does not exist: {self.image_dir}")

        # Load models
        logger.info("Loading embedding models...")
        self.text_model = ModelCache.get_text_model()
        self.clip_model, self.clip_preprocess = ModelCache.get_clip_model()
        self.device = ModelCache.get_device()
        logger.info("Models loaded successfully")

    def generate_text_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text."""
        logger.debug(f"Generating text embedding for: {text[:50]}...")
        return self.text_model.encode(
            text, convert_to_numpy=True, normalize_embeddings=True
        )

    def generate_image_embedding(self, image_path: Path) -> np.ndarray:
        """Generate CLIP embedding for image."""
        logger.debug(f"Generating image embedding for: {image_path}")

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
            logger.warning(f"Error processing image {image_path}: {e}")
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
        logger.debug(f"Generating embedding for restaurant: {restaurant_id}")

        # Text embedding
        text_vec = self.generate_text_embedding(text or "")

        # Image embedding
        img_path = self.image_dir / f"{restaurant_id}.jpg"
        if img_path.exists():
            img_vec = self.generate_image_embedding(img_path)
        else:
            logger.debug(f"No image found for restaurant: {restaurant_id}")
            img_vec = np.zeros((512,))

        # Combine
        return np.concatenate([text_vec, img_vec]).astype("float32")

    def generate_all(self, run_name: str | None = None) -> tuple[np.ndarray, list[str]]:
        """
        Generate embeddings for all restaurants in database.

        Args:
            run_name: Optional name for the MLFlow run.

        Returns:
            Tuple of (embeddings array, list of restaurant IDs).
        """
        logger.info("Starting batch embedding generation")

        restaurants = self.db.get_all_restaurants()
        logger.info(f"Processing {len(restaurants)} restaurants")

        embeddings = []
        meta_ids = []
        errors = 0
        images_found = 0

        # Start MLFlow run if enabled
        if self.use_mlflow:
            experiment_id = MLFlowConfig.get_or_create_experiment(
                MLFlowConfig.EMBEDDING_EXPERIMENT
            )
            mlflow.start_run(experiment_id=experiment_id, run_name=run_name)

            # Log parameters
            mlflow.log_param("total_restaurants", len(restaurants))
            mlflow.log_param("text_model", "all-MiniLM-L6-v2")
            mlflow.log_param("image_model", "CLIP-ViT-B/32")
            mlflow.log_param("text_embedding_dim", 384)
            mlflow.log_param("image_embedding_dim", 512)
            mlflow.log_param("combined_embedding_dim", 896)
            mlflow.log_param("device", str(self.device))
            mlflow.log_param("db_path", str(self.db.db_path))
            mlflow.log_param("image_dir", str(self.image_dir))

        try:
            for i, resto in enumerate(tqdm(restaurants, desc="Generating embeddings")):
                try:
                    text = resto["review_snippet"] or resto["name"] or ""
                    embedding = self.generate_restaurant_embedding(resto["id"], text)

                    embeddings.append(embedding)
                    meta_ids.append(resto["id"])

                    # Track if image was found
                    img_path = self.image_dir / f"{resto['id']}.jpg"
                    if img_path.exists():
                        images_found += 1

                    if (i + 1) % 50 == 0:
                        logger.debug(f"Processed {i + 1}/{len(restaurants)} restaurants")

                except Exception as e:
                    logger.error(f"Error processing restaurant {resto['id']}: {e}")
                    errors += 1
                    continue

            logger.info(
                f"Embedding generation complete: {len(embeddings)} successful, {errors} errors"
            )

            # Log metrics to MLFlow
            if self.use_mlflow:
                mlflow.log_metric("successful_embeddings", len(embeddings))
                mlflow.log_metric("failed_embeddings", errors)
                mlflow.log_metric("images_found", images_found)
                mlflow.log_metric("images_missing", len(restaurants) - images_found)
                mlflow.log_metric("success_rate", len(embeddings) / len(restaurants) if restaurants else 0)
                mlflow.log_metric("image_coverage", images_found / len(restaurants) if restaurants else 0)

                # Log embedding statistics
                embeddings_array = np.vstack(embeddings).astype("float32")
                mlflow.log_metric("embedding_mean", float(np.mean(embeddings_array)))
                mlflow.log_metric("embedding_std", float(np.std(embeddings_array)))
                mlflow.log_metric("embedding_min", float(np.min(embeddings_array)))
                mlflow.log_metric("embedding_max", float(np.max(embeddings_array)))

                logger.info("Metrics logged to MLFlow")

        finally:
            if self.use_mlflow:
                mlflow.end_run()

        return np.vstack(embeddings).astype("float32"), meta_ids
