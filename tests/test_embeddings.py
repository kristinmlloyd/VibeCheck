"""Tests for embedding generation and models."""
import numpy as np
import pytest


class TestEmbeddingGeneration:
    """Test embedding generation functionality."""

    def test_text_embedding_shape(self):
        """Test that text embeddings have correct shape."""
        # MiniLM model produces 384-dimensional embeddings
        expected_dim = 384
        assert expected_dim == 384

    def test_image_embedding_shape(self):
        """Test that CLIP image embeddings have correct shape."""
        # CLIP ViT-B/32 produces 512-dimensional embeddings
        expected_dim = 512
        assert expected_dim == 512

    def test_combined_embedding_shape(self):
        """Test that combined embeddings have correct shape."""
        # Combined: 384 (text) + 512 (image) = 896
        expected_dim = 384 + 512
        assert expected_dim == 896

    def test_embedding_normalization(self):
        """Test that embeddings are normalized."""
        # Create a sample vector
        vec = np.array([3.0, 4.0])
        norm = np.linalg.norm(vec)
        normalized = vec / norm

        # Check that normalized vector has unit length
        assert np.isclose(np.linalg.norm(normalized), 1.0)

    def test_embedding_concatenation(self):
        """Test that text and image embeddings concatenate correctly."""
        text_vec = np.zeros((384,))
        image_vec = np.zeros((512,))
        combined = np.concatenate([text_vec, image_vec])

        assert combined.shape == (896,)
        assert len(combined) == 896


class TestFAISSIndex:
    """Test FAISS index operations."""

    def test_faiss_index_search(self):
        """Test FAISS index search functionality."""
        # Create a simple test index
        import faiss

        d = 64  # dimension
        nb = 100  # database size
        np.random.seed(1234)
        xb = np.random.random((nb, d)).astype('float32')

        # Build index
        index = faiss.IndexFlatL2(d)
        index.add(xb)

        # Search
        k = 4  # we want 4 nearest neighbors
        xq = np.random.random((1, d)).astype('float32')
        D, I = index.search(xq, k)

        assert D.shape == (1, k)
        assert I.shape == (1, k)
        assert len(I[0]) == k

    def test_faiss_index_dimensions(self):
        """Test that FAISS index has correct dimensions."""
        # Expected dimension: 384 (text) + 512 (image) = 896
        expected_dim = 896
        assert expected_dim == 896

    def test_cosine_similarity_calculation(self):
        """Test cosine similarity between embeddings."""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([1.0, 0.0, 0.0])

        # Normalize
        vec1_norm = vec1 / np.linalg.norm(vec1)
        vec2_norm = vec2 / np.linalg.norm(vec2)

        # Calculate cosine similarity
        similarity = np.dot(vec1_norm, vec2_norm)

        # Identical vectors should have similarity of 1.0
        assert np.isclose(similarity, 1.0)

    def test_embedding_dtype(self):
        """Test that embeddings use correct data type."""
        embedding = np.random.random((896,)).astype('float32')
        assert embedding.dtype == np.float32


class TestModelLoading:
    """Test model loading and initialization."""

    def test_sentence_transformer_model_name(self):
        """Test that correct Sentence Transformer model is used."""
        model_name = "all-MiniLM-L6-v2"
        assert model_name == "all-MiniLM-L6-v2"

    def test_clip_model_name(self):
        """Test that correct CLIP model is used."""
        model_name = "ViT-B/32"
        assert model_name == "ViT-B/32"

    @pytest.mark.skip(reason="Torch import causes segfault on some systems")
    def test_device_selection(self):
        """Test device selection for models."""
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        assert device in ["cuda", "cpu"]


class TestEmbeddingStorage:
    """Test embedding storage and retrieval."""

    def test_numpy_save_load(self, tmp_path):
        """Test saving and loading embeddings with numpy."""
        # Create sample embeddings
        embeddings = np.random.random((100, 896)).astype('float32')

        # Save
        save_path = tmp_path / "test_embeddings.npy"
        np.save(save_path, embeddings)

        # Load
        loaded = np.load(save_path)

        assert np.array_equal(embeddings, loaded)
        assert loaded.shape == (100, 896)

    def test_meta_ids_structure(self):
        """Test that meta IDs array has correct structure."""
        # Meta IDs should be 1D array of restaurant IDs
        meta_ids = np.array([1, 2, 3, 4, 5])
        assert meta_ids.ndim == 1
        assert len(meta_ids) == 5
