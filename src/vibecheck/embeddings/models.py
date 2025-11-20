# src/vibecheck/embeddings/models.py

"""Model loading and caching for embeddings."""

import clip
import torch
from sentence_transformers import SentenceTransformer


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
        return cls._device

    @classmethod
    def get_text_model(cls) -> SentenceTransformer:
        """Get or load text embedding model."""
        if cls._text_model is None:
            print("Loading text model...")
            cls._text_model = SentenceTransformer(
                "all-MiniLM-L6-v2", device=cls.get_device()
            )
        return cls._text_model

    @classmethod
    def get_clip_model(cls) -> tuple:
        """Get or load CLIP model and preprocessor."""
        if cls._clip_model is None:
            print("Loading CLIP model...")
            cls._clip_model, cls._clip_preprocess = clip.load(
                "ViT-B/32", device=cls.get_device()
            )
        return cls._clip_model, cls._clip_preprocess
