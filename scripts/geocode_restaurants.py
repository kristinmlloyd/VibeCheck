"""
Geocode Restaurants Using Outscraper API
=========================================
Fetches latitude/longitude coordinates for restaurants using their place_id
via the Outscraper Google Maps API, then stores them in the database.
"""

import os
import sqlite3
import time
from pathlib import Path

from dotenv import load_dotenv
from outscraper import ApiClient
from tqdm import tqdm

# Load environment variables
load_dotenv()

# ==============================================================================
# CONFIG
# ==============================================================================

DATA_DIR = Path("./data")
DB_PATH = Path(os.getenv("DB_PATH", DATA_DIR / "vibecheck.db"))
OUTSCRAPER_API_KEY = os.getenv("OUTSCRAPER_API_KEY")

if not OUTSCRAPER_API_KEY:
    print("❌ Error: OUTSCRAPER_API_KEY not found in environment variables")
    print("   Please add it to your .env file:")
    print("   OUTSCRAPER_API_KEY=your_api_key_here")
    exit(1)

# ==============================================================================
# FUNCTIONS
# ==============================================================================


def add_coordinate_columns():
    """Add latitude and longitude columns to restaurants table if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE restaurants ADD COLUMN latitude REAL")
        cursor.execute("ALTER TABLE restaurants ADD COLUMN longitude REAL")
        print("✅ Added latitude and longitude columns to database")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("ℹ️  Latitude and longitude columns already exist")
        else:
            raise e

    conn.commit()
    conn.close()


def get_restaurants_without_coordinates():
    """Get all restaurants that need geocoding."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, name, place_id, address
        FROM restaurants
        WHERE place_id IS NOT NULL
        AND (latitude IS NULL OR longitude IS NULL)
        ORDER BY id
        """
    )

    restaurants = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return restaurants


def geocode_with_outscraper(place_ids, api_client):
    """
    Geocode multiple place_ids using Outscraper API.

    Args:
        place_ids: List of Google Place IDs
        api_client: Outscraper API client

    Returns:
        Dictionary mapping place_id to (latitude, longitude) tuples
    """
    results = {}

    try:
        print(f"🔄 Requesting coordinates for {len(place_ids)} place_ids...")

        # Use google_maps_reviews_v2 which accepts place_ids directly
        # This endpoint provides place details including coordinates
        response = api_client.google_maps_reviews_v2(
            place_ids,
            reviews_limit=0,  # We don't need reviews, just coordinates
            language="en",
        )

        print(
            f"📥 Received response, parsing {len(response) if response else 0} results..."
        )

        # Parse response
        if response:
            for place_data in response:
                if isinstance(place_data, dict):
                    place_id = place_data.get("place_id")
                    lat = place_data.get("latitude")
                    lng = place_data.get("longitude")

                    if place_id and lat is not None and lng is not None:
                        results[place_id] = (float(lat), float(lng))
                        print(f"  ✓ {place_id[:20]}... -> ({lat:.6f}, {lng:.6f})")

        print(f"✅ Successfully parsed {len(results)} coordinates from this batch")

    except Exception as e:
        print(f"❌ Outscraper API error: {e}")
        import traceback

        traceback.print_exc()

    return results


def update_coordinates(restaurant_id, latitude, longitude):
    """Update restaurant coordinates in database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE restaurants
        SET latitude = ?, longitude = ?
        WHERE id = ?
        """,
        (latitude, longitude, restaurant_id),
    )

    conn.commit()
    conn.close()


def geocode_all_restaurants():
    """Main function to geocode all restaurants."""
    print("\n" + "=" * 60)
    print("🌍 GEOCODING RESTAURANTS WITH OUTSCRAPER API")
    print("=" * 60)

    # Add coordinate columns if needed
    add_coordinate_columns()

    # Get restaurants that need geocoding
    restaurants = get_restaurants_without_coordinates()
    print(f"\n📍 Found {len(restaurants)} restaurants to geocode")

    if not restaurants:
        print("✅ All restaurants already have coordinates!")
        return

    # Initialize Outscraper API client
    api_client = ApiClient(api_key=OUTSCRAPER_API_KEY)

    # Process in batches to respect API rate limits
    BATCH_SIZE = 50  # Process more at once for speed
    success_count = 0
    fail_count = 0

    for i in tqdm(range(0, len(restaurants), BATCH_SIZE), desc="Geocoding batches"):
        batch = restaurants[i : i + BATCH_SIZE]
        place_ids = [r["place_id"] for r in batch]

        # Geocode batch
        coordinates = geocode_with_outscraper(place_ids, api_client)

        # Update database
        for restaurant in batch:
            place_id = restaurant["place_id"]

            if place_id in coordinates:
                lat, lng = coordinates[place_id]
                update_coordinates(restaurant["id"], lat, lng)
                success_count += 1
                # Only print every 10th success to reduce output
                if success_count % 10 == 0:
                    print(f"✅ Geocoded {success_count} restaurants...")
            else:
                fail_count += 1

        # Commit every batch for progress persistence
        if success_count % 50 == 0:
            print(f"💾 Progress saved: {success_count} successful, {fail_count} failed")

        # Rate limiting - smaller delay
        if i + BATCH_SIZE < len(restaurants):
            time.sleep(1)  # Reduced to 1 second

    # Summary
    print("\n" + "=" * 60)
    print("📊 GEOCODING SUMMARY")
    print("=" * 60)
    print(f"✅ Successfully geocoded: {success_count} restaurants")
    print(f"❌ Failed to geocode: {fail_count} restaurants")
    print(f"📍 Total processed: {success_count + fail_count}")
    print("=" * 60 + "\n")


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        print("   Please check the path and try again.")
        exit(1)

    print(f"Using database: {DB_PATH}")
    geocode_all_restaurants()
