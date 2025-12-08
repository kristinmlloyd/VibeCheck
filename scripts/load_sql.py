"""
Load VibeCheck scraped data into SQLite database
=================================================
Reads the JSON output from vibecheck_full_dc.py and loads it into SQL.

Usage:
    python load_vibecheck_to_sql.py
"""

import json
import sqlite3
from pathlib import Path

# ==============================================================================
# CONFIG
# ==============================================================================

INPUT_DIR = Path("./vibecheck_full_output")
RESULTS_FILE = INPUT_DIR / "vibecheck_results.json"
DB_PATH = INPUT_DIR / "vibecheck.db"

# ==============================================================================
# DATABASE SETUP
# ==============================================================================

def init_database():
    """Initialize SQLite database with proper schema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Main restaurants table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS restaurants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            place_id TEXT UNIQUE NOT NULL,
            data_id TEXT,
            address TEXT,
            rating REAL,
            reviews_count INTEGER
        )
    """)
    
    # Reviews table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_id INTEGER,
            review_text TEXT,
            likes INTEGER DEFAULT 0,
            FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
        )
    """)
    
    # Vibe photos table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vibe_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_id INTEGER,
            photo_url TEXT,
            local_filename TEXT,
            FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
        )
    """)
    
    # Vibe analysis table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vibe_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_id INTEGER,
            vibe_name TEXT,
            mention_count INTEGER,
            FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
        )
    """)
    
    conn.commit()
    return conn


def load_data_to_db(conn, data):
    """Load JSON data into database."""
    cursor = conn.cursor()
    
    restaurants_loaded = 0
    reviews_loaded = 0
    photos_loaded = 0
    vibes_loaded = 0
    
    for restaurant in data:
        info = restaurant.get("info", {})
        
        # Insert restaurant
        cursor.execute("""
            INSERT OR IGNORE INTO restaurants 
            (name, place_id, data_id, address, rating, reviews_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            info.get("name"),
            info.get("place_id"),
            info.get("data_id"),
            info.get("address"),
            info.get("rating"),
            info.get("reviews_count")
        ))
        
        restaurant_id = cursor.lastrowid
        if restaurant_id == 0:  # Already exists, get the id
            cursor.execute("SELECT id FROM restaurants WHERE place_id = ?", 
                          (info.get("place_id"),))
            restaurant_id = cursor.fetchone()[0]
        else:
            restaurants_loaded += 1
        
        # Insert reviews
        for review in restaurant.get("reviews", []):
            cursor.execute("""
                INSERT INTO reviews (restaurant_id, review_text, likes)
                VALUES (?, ?, ?)
            """, (
                restaurant_id,
                review.get("text", ""),
                review.get("likes", 0)
            ))
            reviews_loaded += 1
        
        # Insert vibe photos
        photo_urls = restaurant.get("vibe_photos", [])
        downloaded_files = restaurant.get("downloaded_files", [])
        
        for i, url in enumerate(photo_urls):
            local_file = downloaded_files[i] if i < len(downloaded_files) else None
            cursor.execute("""
                INSERT INTO vibe_photos (restaurant_id, photo_url, local_filename)
                VALUES (?, ?, ?)
            """, (restaurant_id, url, local_file))
            photos_loaded += 1
        
        # Insert vibe analysis
        vibe_data = restaurant.get("vibe_analysis", {})
        top_vibes = vibe_data.get("top_vibes", [])
        
        for vibe_name, count in top_vibes:
            cursor.execute("""
                INSERT INTO vibe_analysis (restaurant_id, vibe_name, mention_count)
                VALUES (?, ?, ?)
            """, (restaurant_id, vibe_name, count))
            vibes_loaded += 1
    
    conn.commit()
    
    return {
        "restaurants": restaurants_loaded,
        "reviews": reviews_loaded,
        "photos": photos_loaded,
        "vibes": vibes_loaded
    }


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("\n" + "=" * 60)
    print("📊 LOADING VIBECHECK DATA INTO SQL")
    print("=" * 60)
    
    # Check if results file exists
    if not RESULTS_FILE.exists():
        print(f"\n❌ Results file not found: {RESULTS_FILE}")
        print("   Make sure you've run vibecheck_full_dc.py first!")
        return
    
    # Load JSON data
    print(f"\n📂 Reading data from {RESULTS_FILE}...")
    with open(RESULTS_FILE) as f:
        data = json.load(f)
    
    print(f"✅ Loaded {len(data)} restaurants from JSON")
    
    # Initialize database
    print(f"\n🗄️  Initializing database: {DB_PATH}")
    conn = init_database()
    
    # Load data
    print("\n📥 Loading data into database...")
    stats = load_data_to_db(conn, data)
    
    conn.close()
    
    # Print summary
    print("\n" + "=" * 60)
    print("✅ DATA LOAD COMPLETE")
    print("=" * 60)
    print(f"🍽️  Restaurants: {stats['restaurants']}")
    print(f"📝 Reviews: {stats['reviews']}")
    print(f"📷 Photos: {stats['photos']}")
    print(f"✨ Vibe entries: {stats['vibes']}")
    print(f"\n📁 Database: {DB_PATH}")
    print("\nYou can now query the database with:")
    print(f"  sqlite3 {DB_PATH}")


if __name__ == "__main__":
    main()