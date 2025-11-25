# src/vibecheck/embeddings/models.py

"""Model loading and caching for embeddings."""

import clip
import torch
from sentence_transformers import SentenceTransformer

from vibecheck.logging_config import get_logger

logger = get_logger(__name__)


class ModelCache:
    """Cache for pre-trained models to avoid reloading."""

    _text_model = None
    _clip_model = None
    _clip_preprocess = None
    _device = None

    @classmethod
    def get_device(cls) -> str:
        """Get computing device (cuda or cpu)."""
        if cls._device is None:
            cls._device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {cls._device}")
        return cls._device

    @classmethod
    def get_text_model(cls) -> SentenceTransformer:
        """Get or load text embedding model."""
        if cls._text_model is None:
            logger.info("Loading text model (all-MiniLM-L6-v2)...")
            try:
                cls._text_model = SentenceTransformer(
                    "all-MiniLM-L6-v2", device=cls.get_device()
                )
                logger.info("Text model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load text model: {e}")
                raise
        return cls._text_model

    @classmethod
    def get_clip_model(cls) -> tuple:
        """Get or load CLIP model and preprocessor."""
        if cls._clip_model is None:
            logger.info("Loading CLIP model (ViT-B/32)...")
            try:
                cls._clip_model, cls._clip_preprocess = clip.load(
                    "ViT-B/32", device=cls.get_device()
                )
                logger.info("CLIP model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load CLIP model: {e}")
                raise
        return cls._clip_model, cls._clip_preprocess

    @classmethod
    def clear_cache(cls):
        """Clear all cached models to free memory."""
        logger.info("Clearing model cache")
        cls._text_model = None
        cls._clip_model = None
        cls._clip_preprocess = None
        cls._device = None
        logger.debug("Model cache cleared")
