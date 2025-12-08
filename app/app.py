"""
VibeCheck Flask Application
============================
Main Flask backend for restaurant vibe search and visualization.
"""

import os
import sqlite3
from io import BytesIO
from pathlib import Path

import clip
import faiss
import numpy as np
import torch
from flask import Flask, jsonify, render_template, request
from PIL import Image
from sentence_transformers import SentenceTransformer

# ==============================================================================
# CONFIG
# ==============================================================================

# Get the app directory (where this file is located)
APP_DIR = Path(__file__).parent
# Data directory is one level up from app/
DATA_DIR = APP_DIR.parent / "data"

# Data file paths (with environment variable overrides for Docker)
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", DATA_DIR))
DB_PATH = Path(os.getenv("DB_PATH", DATA_DIR / "vibecheck.db"))
IMAGE_DIR = Path(os.getenv("IMAGE_DIR", DATA_DIR / "images"))
FAISS_PATH = Path(os.getenv("FAISS_PATH", DATA_DIR / "vibecheck_index.faiss"))
META_PATH = Path(os.getenv("META_PATH", DATA_DIR / "meta_ids.npy"))
VIBE_MAP_CSV = Path(os.getenv("VIBE_MAP_CSV", DATA_DIR / "vibe_map.csv"))

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ==============================================================================
# FLASK APP
# ==============================================================================

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

# ==============================================================================
# LOAD MODELS (once at startup)
# ==============================================================================

print("Loading models...")
text_model = SentenceTransformer("all-MiniLM-L6-v2", device=DEVICE)
clip_model, clip_preprocess = clip.load("ViT-B/32", device=DEVICE)
faiss_index = faiss.read_index(str(FAISS_PATH))
meta_ids = np.load(META_PATH)
print(f"Models loaded. FAISS index contains {len(meta_ids)} restaurants.")

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def encode_query(text=None, image_file=None):
    """Encode text and/or image query into combined embedding."""

    # Encode text
    text_vec = text_model.encode(
        text or "", convert_to_numpy=True, normalize_embeddings=True
    )

    # Encode image if provided
    if image_file:
        try:
            img = Image.open(BytesIO(image_file)).convert("RGB")
            img_tensor = clip_preprocess(img).unsqueeze(0).to(DEVICE)
            with torch.no_grad():
                img_vec = clip_model.encode_image(img_tensor)
            img_vec /= img_vec.norm(dim=-1, keepdim=True)
            img_vec = img_vec.cpu().numpy()[0]
        except Exception as e:
            print(f"Error processing image: {e}")
            img_vec = np.zeros((512,))
    else:
        img_vec = np.zeros((512,))

    # Combine embeddings
    combined = np.concatenate([text_vec, img_vec]).astype("float32")
    return combined[None, :]


def get_restaurant_details(restaurant_id, full_details=False):
    """Fetch restaurant details from database."""
    conn = get_db()
    cursor = conn.cursor()

    # Basic info
    cursor.execute(
        """
        SELECT id, name, rating, address, reviews_count, place_id
        FROM restaurants
        WHERE id = ?
        """,
        (restaurant_id,),
    )

    row = cursor.fetchone()
    if not row:
        return None

    restaurant = dict(row)

    # Photos - get first photo for search results, or all 5 for full details
    photo_limit = 5 if full_details else 1
    cursor.execute(
        """
        SELECT local_filename, photo_url
        FROM vibe_photos
        WHERE restaurant_id = ?
        LIMIT ?
        """,
        (restaurant_id, photo_limit),
    )

    photos = cursor.fetchall()
    if full_details:
        restaurant["photos"] = [
            {"filename": p["local_filename"], "url": p["photo_url"]} for p in photos
        ]
    else:
        # For search results, just return first photo
        restaurant["photo_filename"] = photos[0]["local_filename"] if photos else None
        restaurant["photo_url"] = photos[0]["photo_url"] if photos else None

    # Vibes
    cursor.execute(
        """
        SELECT vibe_name, mention_count
        FROM vibe_analysis
        WHERE restaurant_id = ?
        ORDER BY mention_count DESC
        LIMIT 3
        """,
        (restaurant_id,),
    )

    vibes = cursor.fetchall()
    restaurant["vibes"] = [
        {"name": v["vibe_name"], "count": v["mention_count"]} for v in vibes
    ]

    # Reviews - get 2 for search results, or 5 for full details
    review_limit = 5 if full_details else 2
    cursor.execute(
        """
        SELECT review_text, likes
        FROM reviews
        WHERE restaurant_id = ?
        ORDER BY likes DESC
        LIMIT ?
        """,
        (restaurant_id, review_limit),
    )

    reviews = cursor.fetchall()
    if full_details:
        restaurant["reviews"] = [
            {"text": r["review_text"], "likes": r["likes"]} for r in reviews
        ]
    else:
        restaurant["reviews"] = [
            {"text": r["review_text"][:200] + "...", "likes": r["likes"]}
            for r in reviews
        ]

    conn.close()
    return restaurant


def get_all_restaurants_for_map():
    """Fetch all restaurants with coordinates for map visualization."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT r.id, r.name, r.rating, r.address, r.reviews_count,
               vm.x, vm.y, vm.cluster
        FROM restaurants r
        LEFT JOIN (
            SELECT id, name, x, y, cluster
            FROM vibe_map_data
        ) vm ON r.name = vm.name
        WHERE r.rating IS NOT NULL
    """)

    restaurants = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return restaurants


def import_vibe_map_to_db():
    """Load vibe_map.csv into database."""
    import pandas as pd

    if not VIBE_MAP_CSV.exists():
        return

    conn = get_db()
    df = pd.read_csv(VIBE_MAP_CSV)
    df.to_sql("vibe_map_data", conn, if_exists="replace", index=False)
    conn.close()
    print("Imported vibe_map.csv into database.")


# ==============================================================================
# ROUTES
# ==============================================================================


@app.route("/")
def index():
    """Main page."""
    return render_template("index.html")


@app.route("/api/search", methods=["POST"])
def search():
    """Search restaurants via FAISS index."""
    try:
        query_text = request.form.get("text", "")
        query_image = request.files.get("image")
        top_k = int(request.form.get("top_k", 9))

        if not query_text and not query_image:
            return jsonify({"error": "Please provide text or image query"}), 400

        image_bytes = query_image.read() if query_image else None
        query_vec = encode_query(query_text, image_bytes)

        distances, indices = faiss_index.search(query_vec, top_k)

        results = []
        for idx, distance in zip(indices[0], distances[0], strict=False):
            restaurant_id = int(meta_ids[idx])
            details = get_restaurant_details(restaurant_id)
            if details:
                details["similarity_score"] = float(distance)
                results.append(details)

        return jsonify({"results": results})

    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/restaurant/<int:restaurant_id>")
def get_restaurant(restaurant_id):
    """Get full restaurant details with all photos and reviews."""
    details = get_restaurant_details(restaurant_id, full_details=True)
    if details:
        return jsonify(details)
    return jsonify({"error": "Restaurant not found"}), 404


@app.route("/api/map-data")
def map_data():
    try:
        restaurants = get_all_restaurants_for_map()
        return jsonify({"restaurants": restaurants})
    except Exception as e:
        print(f"Map data error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/vibe-stats")
def vibe_stats():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT vibe_name, SUM(mention_count) as total
        FROM vibe_analysis
        GROUP BY vibe_name
        ORDER BY total DESC
        LIMIT 10
    """)

    vibes = [{"name": row[0], "count": row[1]} for row in cursor.fetchall()]
    conn.close()

    return jsonify({"vibes": vibes})


@app.route("/images/<path:filename>")
def serve_image(filename):
    from flask import send_from_directory

    return send_from_directory(IMAGE_DIR, filename)


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    import_vibe_map_to_db()

    port = int(os.getenv("FLASK_PORT", 8080))

    print("\n" + "=" * 60)
    print("VibeCheck Flask App Starting")
    print("=" * 60)
    print(f"Restaurants loaded: {len(meta_ids)}")
    print(f"Server available at http://localhost:{port}")
    print("=" * 60 + "\n")

    app.run(debug=True, host="0.0.0.0", port=port)
