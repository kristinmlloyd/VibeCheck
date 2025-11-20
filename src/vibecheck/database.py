# src/vibecheck/database.py
# creates internal API models

"""Database operations for VibeCheck."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any


class RestaurantDatabase:
    """
    Interface for restaurant database operations.

    Example:
        >>> db = RestaurantDatabase("data/raw/restaurants.db")
        >>> info = db.get_restaurant("some_id")
        >>> print(info['name'])
    """

    def __init__(self, db_path: Path = Path("data/raw/restaurants.db")):
        """Initialize database connection."""
        self.db_path = Path(db_path)

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def get_restaurant(self, restaurant_id: str) -> dict[str, Any] | None:
        """
        Get restaurant information by ID.

        Args:
            restaurant_id: Unique restaurant identifier.

        Returns:
            Dictionary with restaurant info or None if not found.
        """
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT id, name, rating, address, image_url, categories, review_snippet "
                "FROM restaurants WHERE id=?",
                (restaurant_id,),
            ).fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "name": row[1],
            "rating": row[2],
            "address": row[3],
            "image_url": row[4],
            "categories": row[5],
            "review_snippet": row[6],
        }

    def get_all_restaurants(self) -> list[dict[str, Any]]:
        """Get all restaurants from database."""
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT id, name, rating, review_snippet FROM restaurants"
            ).fetchall()

        return [
            {"id": row[0], "name": row[1], "rating": row[2], "review_snippet": row[3]}
            for row in rows
        ]
