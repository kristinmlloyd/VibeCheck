"""Database operations for VibeCheck."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from vibecheck.logging_config import get_logger

logger = get_logger(__name__)


class RestaurantDatabase:
    """
    Interface for restaurant database operations.

    Example:
        >>> db = RestaurantDatabase("data/restaurants_info/restaurants.db")
        >>> info = db.get_restaurant("some_id")
        >>> print(info['name'])
    """

    def __init__(self, db_path: Path = Path("data/restaurants_info/restaurants.db")):
        """Initialize database connection."""
        self.db_path = Path(db_path)
        logger.info(f"Initialized database connection: {self.db_path}")

        if not self.db_path.exists():
            logger.warning(f"Database file does not exist: {self.db_path}")

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        logger.debug(f"Opening database connection: {self.db_path}")
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
            logger.debug("Database connection closed")

    def get_restaurant(self, restaurant_id: str) -> dict[str, Any] | None:
        """
        Get restaurant information by ID.

        Args:
            restaurant_id: Unique restaurant identifier.

        Returns:
            Dictionary with restaurant info or None if not found.
        """
        logger.debug(f"Fetching restaurant: {restaurant_id}")

        try:
            with self.get_connection() as conn:
                row = conn.execute(
                    "SELECT id, name, rating, address, image_url, categories, review_snippet "
                    "FROM restaurants WHERE id=?",
                    (restaurant_id,),
                ).fetchone()

            if not row:
                logger.debug(f"Restaurant not found: {restaurant_id}")
                return None

            result = {
                "id": row[0],
                "name": row[1],
                "rating": row[2],
                "address": row[3],
                "image_url": row[4],
                "categories": row[5],
                "review_snippet": row[6],
            }
            logger.debug(f"Found restaurant: {result['name']}")
            return result

        except sqlite3.Error as e:
            logger.error(f"Database error fetching restaurant {restaurant_id}: {e}")
            return None

    def get_all_restaurants(self) -> list[dict[str, Any]]:
        """Get all restaurants from database."""
        logger.info("Fetching all restaurants from database")

        try:
            with self.get_connection() as conn:
                rows = conn.execute(
                    "SELECT id, name, rating, review_snippet FROM restaurants"
                ).fetchall()

            restaurants = [
                {
                    "id": row[0],
                    "name": row[1],
                    "rating": row[2],
                    "review_snippet": row[3],
                }
                for row in rows
            ]

            logger.info(f"Retrieved {len(restaurants)} restaurants")
            return restaurants

        except sqlite3.Error as e:
            logger.error(f"Database error fetching all restaurants: {e}")
            return []
