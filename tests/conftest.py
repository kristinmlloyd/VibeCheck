"""Pytest configuration and shared fixtures."""
import os
import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_restaurant_data():
    """Sample restaurant data for testing."""
    return {
        "id": 1,
        "name": "Test Restaurant",
        "rating": 4.5,
        "address": "123 Test St, Washington, DC 20001",
        "reviews_count": 100,
        "place_id": "test_place_id",
    }


@pytest.fixture
def sample_review_data():
    """Sample review data for testing."""
    return [
        {"review_text": "Great food and atmosphere!", "likes": 50},
        {"review_text": "Amazing service and cozy vibe.", "likes": 30},
    ]


@pytest.fixture
def sample_vibe_data():
    """Sample vibe data for testing."""
    return [
        {"vibe_name": "Cozy/Intimate", "mention_count": 10},
        {"vibe_name": "Romantic/Date Night", "mention_count": 8},
        {"vibe_name": "Upscale/Fancy", "mention_count": 5},
    ]


@pytest.fixture
def mock_db(monkeypatch, tmp_path):
    """Create a temporary test database."""
    import sqlite3

    db_path = tmp_path / "test_vibecheck.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE restaurants (
            id INTEGER PRIMARY KEY,
            name TEXT,
            rating REAL,
            address TEXT,
            reviews_count INTEGER,
            place_id TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE reviews (
            id INTEGER PRIMARY KEY,
            restaurant_id INTEGER,
            review_text TEXT,
            likes INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE vibe_analysis (
            id INTEGER PRIMARY KEY,
            restaurant_id INTEGER,
            vibe_name TEXT,
            mention_count INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE vibe_photos (
            id INTEGER PRIMARY KEY,
            restaurant_id INTEGER,
            local_filename TEXT,
            photo_url TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE vibe_map_data (
            id INTEGER PRIMARY KEY,
            name TEXT,
            rating REAL,
            address TEXT,
            review_count INTEGER,
            x REAL,
            y REAL,
            cluster INTEGER
        )
    """)

    conn.commit()
    conn.close()

    return db_path
