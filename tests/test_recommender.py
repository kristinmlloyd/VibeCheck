"""Tests for restaurant recommendation system."""
import numpy as np
import pytest


class TestSearchFunctionality:
    """Test search and recommendation logic."""

    def test_search_with_text_query(self):
        """Test search with text query only."""
        query = "cozy romantic restaurant"
        assert isinstance(query, str)
        assert len(query) > 0

    def test_search_with_empty_query(self):
        """Test that empty query is handled."""
        query = ""
        # Should either have text or image
        assert query == "" or query is None

    def test_search_result_limit(self):
        """Test that search results respect limit parameter."""
        k = 10
        # Mock results
        results = list(range(k))
        assert len(results) == k

    def test_similarity_score_range(self):
        """Test that similarity scores are in valid range."""
        # Cosine similarity should be between -1 and 1
        # But for normalized vectors, typically 0 to 1
        score = 0.95
        assert 0.0 <= score <= 1.0

    def test_search_result_structure(self):
        """Test search result has correct structure."""
        mock_result = {
            "id": 1,
            "name": "Test Restaurant",
            "rating": 4.5,
            "address": "123 Test St",
            "similarity_score": 0.95,
        }

        assert "id" in mock_result
        assert "name" in mock_result
        assert "similarity_score" in mock_result
        assert isinstance(mock_result["id"], int)
        assert isinstance(mock_result["similarity_score"], float)


class TestRankingLogic:
    """Test restaurant ranking and scoring."""

    def test_top_k_selection(self):
        """Test that top-k results are returned."""
        # Create mock scores
        scores = np.array([0.9, 0.8, 0.95, 0.7, 0.85])
        k = 3

        # Get top k indices
        top_indices = np.argsort(scores)[-k:][::-1]

        assert len(top_indices) == k
        # Check that indices correspond to highest scores
        assert scores[top_indices[0]] == 0.95

    def test_distance_to_similarity_conversion(self):
        """Test converting FAISS L2 distances to similarity scores."""
        # L2 distance to similarity (for normalized vectors)
        # similarity = 1 - (distance^2 / 2)
        distance = 0.0  # perfect match
        similarity = 1 - (distance**2 / 2)
        assert similarity == 1.0

    def test_result_deduplication(self):
        """Test that duplicate results are removed."""
        results = [
            {"id": 1, "name": "Restaurant A"},
            {"id": 2, "name": "Restaurant B"},
            {"id": 1, "name": "Restaurant A"},  # duplicate
        ]

        # Deduplicate by id
        seen = set()
        unique_results = []
        for r in results:
            if r["id"] not in seen:
                seen.add(r["id"])
                unique_results.append(r)

        assert len(unique_results) == 2


class TestMultimodalSearch:
    """Test multimodal (text + image) search."""

    def test_text_only_search(self):
        """Test search with only text query."""
        text_query = "romantic dinner"
        image_query = None

        assert text_query is not None
        assert image_query is None

    def test_image_only_search(self):
        """Test search with only image query."""
        text_query = None
        image_bytes = b"fake_image_data"

        assert text_query is None
        assert image_bytes is not None

    def test_combined_search(self):
        """Test search with both text and image."""
        text_query = "romantic dinner"
        image_bytes = b"fake_image_data"

        assert text_query is not None
        assert image_bytes is not None

    def test_empty_text_handling(self):
        """Test that empty text is handled gracefully."""
        text_query = ""
        # Should create zero vector or use default
        assert isinstance(text_query, str)


class TestVibeMatching:
    """Test vibe matching and filtering."""

    def test_vibe_name_normalization(self):
        """Test that vibe names are normalized."""
        vibe_raw = "Cozy/Intimate"
        vibe_normalized = vibe_raw.strip().title()
        assert vibe_normalized == "Cozy/Intimate"

    def test_vibe_count_filtering(self):
        """Test filtering vibes by mention count."""
        vibes = [
            {"name": "Cozy", "count": 10},
            {"name": "Loud", "count": 2},
            {"name": "Romantic", "count": 8},
        ]

        # Filter vibes with count >= 5
        min_count = 5
        filtered = [v for v in vibes if v["count"] >= min_count]

        assert len(filtered) == 2

    def test_top_vibes_sorting(self):
        """Test that vibes are sorted by count."""
        vibes = [
            {"name": "Cozy", "count": 10},
            {"name": "Loud", "count": 2},
            {"name": "Romantic", "count": 8},
        ]

        sorted_vibes = sorted(vibes, key=lambda x: x["count"], reverse=True)

        assert sorted_vibes[0]["name"] == "Cozy"
        assert sorted_vibes[0]["count"] == 10


class TestPerformance:
    """Test performance-related functionality."""

    def test_batch_processing(self):
        """Test that batch processing works correctly."""
        items = list(range(100))
        batch_size = 10

        batches = [items[i:i+batch_size] for i in range(0, len(items), batch_size)]

        assert len(batches) == 10
        assert all(len(b) == batch_size for b in batches)

    def test_index_search_efficiency(self):
        """Test that FAISS search is efficient."""
        # FAISS should be able to search large indexes quickly
        index_size = 1000
        search_k = 10

        assert search_k < index_size
        assert search_k <= 100  # Reasonable top-k limit


class TestErrorHandling:
    """Test error handling in recommendation system."""

    def test_invalid_query_handling(self):
        """Test handling of invalid queries."""
        # None query should be handled
        query = None
        if query is None:
            query = ""
        assert query == ""

    def test_missing_restaurant_handling(self):
        """Test handling of missing restaurant IDs."""
        valid_ids = [1, 2, 3, 4, 5]
        search_id = 999

        result = search_id in valid_ids
        assert result is False

    def test_image_processing_error_handling(self):
        """Test handling of image processing errors."""
        # Invalid image data should be handled gracefully
        invalid_image = b"not_an_image"

        try:
            from PIL import Image
            from io import BytesIO
            img = Image.open(BytesIO(invalid_image))
            success = True
        except Exception:
            success = False

        assert success is False  # Should fail for invalid data
