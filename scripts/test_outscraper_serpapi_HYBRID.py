"""
VibeCheck: SerpApi Vibe Photos + Outscraper Reviews
====================================================
Uses Google Maps' native "Vibe" photo category filtering via SerpApi.
Only keeps restaurants with 5+ vibe photos.
"""

import json
import os
import re
from collections import defaultdict
from pathlib import Path

import requests
from outscraper import ApiClient

# ==============================================================================
# CONFIG
# ==============================================================================

OUTSCRAPER_API_KEY = os.getenv(
    "OUTSCRAPER_API_KEY", "NDA1NWE2OTY1YzJkNDE1MDljM2MyMDVkZGY3NGQ4MjJ8YWE3OTNhM2I4Zg"
)
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "FILL IN HERE")  ### FILL in here!!!!

# Google Maps photo category IDs
VIBE_CATEGORY_ID = "CgIYIg=="  # Interior/Atmosphere photos

# Hard limits
REVIEWS_NEEDED = 5
IMAGES_NEEDED = 5

# Test restaurants (10 DC spots)
TEST_RESTAURANTS = [
    "Le Diplomate Washington DC",
    "Bar Chinois Washington DC",
    "The Tombs Georgetown DC",
    "Tail Up Goat Washington DC",
    "Rose's Luxury Washington DC",
    "Maydan Washington DC",
    "Rasika Washington DC",
    "Bad Saint Washington DC",
    "Fiola Mare Washington DC",
    "The Dabney Washington DC",
]

# Output paths
OUTPUT_DIR = Path("./vibecheck_output")
IMAGES_DIR = OUTPUT_DIR / "images"
CHECKPOINT_FILE = OUTPUT_DIR / "checkpoint.json"  # Tracks progress across teammates

# ==============================================================================
# CHECKPOINT FUNCTIONS
# ==============================================================================


def load_checkpoint() -> dict:
    """Load checkpoint from file. Returns dict with processed restaurants."""
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE) as f:
            return json.load(f)
    return {"processed": [], "results": [], "skipped": []}


def save_checkpoint(checkpoint: dict):
    """Save checkpoint to file after each restaurant."""
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(checkpoint, f, indent=2, default=str)


# ==============================================================================
# VIBE PATTERNS (for review analysis)
# ==============================================================================

VIBE_PATTERNS = {
    "dim_lighting": {
        "display_name": "Dim/Romantic Lighting",
        "patterns": [r"\bdim\b", r"\bcandle", r"\bmoody\b", r"\bambient\b"],
    },
    "loud_noisy": {
        "display_name": "Loud/Noisy",
        "patterns": [r"\bloud\b", r"\bnoisy\b", r"\bbustling\b"],
    },
    "quiet_intimate": {
        "display_name": "Quiet/Intimate",
        "patterns": [r"\bquiet\b", r"\bintimate\b", r"\bpeaceful\b"],
    },
    "lively_energetic": {
        "display_name": "Lively/Energetic",
        "patterns": [r"\blively\b", r"\bbuzz\b", r"\bvibrant\b", r"\bscene\b"],
    },
    "chill_relaxed": {
        "display_name": "Chill/Relaxed",
        "patterns": [r"\bchill\b", r"\brelax", r"\bcozy\b", r"\bcomfort"],
    },
    "upscale_fancy": {
        "display_name": "Upscale/Fancy",
        "patterns": [r"\bupscale\b", r"\bfancy\b", r"\belegant\b", r"\bchic\b"],
    },
    "casual": {
        "display_name": "Casual/Divey",
        "patterns": [r"\bcasual\b", r"\bdive\b", r"\bneighborhood\b"],
    },
    "romantic": {
        "display_name": "Romantic/Date Night",
        "patterns": [r"\bromantic\b", r"\bdate\b", r"\banniversary\b"],
    },
    "outdoor": {
        "display_name": "Outdoor/Patio",
        "patterns": [r"\boutdoor\b", r"\bpatio\b", r"\brooftop\b", r"\bterrace\b"],
    },
}

# ==============================================================================
# SERPAPI: Fetch vibe photos
# ==============================================================================


def get_vibe_photos_serpapi(google_id: str, limit: int = 10) -> list[dict]:
    """
    Fetch VIBE-category photos from Google Maps via SerpApi.

    Args:
        google_id: The data_id (e.g., "0x89c25998e556791b:0xbdcd67f46e37b16d")
        limit: Max photos to return

    Returns:
        List of photo dicts with URLs
    """
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_maps_photos",
        "data_id": google_id,
        "category_id": VIBE_CATEGORY_ID,
        "hl": "en",
        "api_key": SERPAPI_API_KEY,
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()

        if "error" in data:
            print(f"      ❌ SerpApi error: {data['error']}")
            return []

        photos = []
        for photo in data.get("photos", [])[:limit]:
            photos.append(
                {
                    "url": photo.get("image"),
                    "thumbnail": photo.get("thumbnail"),
                }
            )

        return photos

    except Exception as e:
        print(f"      ❌ SerpApi error: {e}")
        return []


# ==============================================================================
# OUTSCRAPER: Place data and reviews
# ==============================================================================


def get_restaurant_data(client: ApiClient, query: str) -> dict | None:
    """Search for a restaurant and get basic info."""
    try:
        results = client.google_maps_search(query, limit=1, language="en", region="us")

        if results and len(results) > 0:
            places = results[0] if isinstance(results[0], list) else results
            if places:
                place = places[0]
                return {
                    "name": place.get("name"),
                    "place_id": place.get("place_id"),
                    "google_id": place.get("google_id"),
                    "address": place.get("full_address") or place.get("address"),
                    "rating": place.get("rating"),
                    "reviews_count": place.get("reviews"),
                }
    except Exception as e:
        print(f"      ❌ Search error: {e}")

    return None


def get_reviews(client: ApiClient, place_id: str, limit: int = 5) -> list[dict]:
    """Fetch reviews sorted by likes."""
    try:
        results = client.google_maps_reviews(
            [place_id],
            reviews_limit=limit,
            language="en",
            sort="most_relevant",
        )

        if results and len(results) > 0:
            reviews = results[0].get("reviews_data", [])
            return sorted(
                reviews, key=lambda x: x.get("review_likes") or 0, reverse=True
            )[:limit]
    except Exception as e:
        print(f"      ❌ Reviews error: {e}")

    return []


# ==============================================================================
# HELPERS
# ==============================================================================


def analyze_vibes(reviews: list[dict]) -> dict:
    """Analyze reviews for vibe mentions."""
    compiled = {
        cat: [re.compile(p, re.IGNORECASE) for p in cfg["patterns"]]
        for cat, cfg in VIBE_PATTERNS.items()
    }

    counts = defaultdict(int)

    for review in reviews:
        text = review.get("review_text", "") or ""
        for category, patterns in compiled.items():
            for pattern in patterns:
                if pattern.search(text):
                    counts[category] += 1
                    break

    sorted_vibes = sorted(
        [(VIBE_PATTERNS[cat]["display_name"], count) for cat, count in counts.items()],
        key=lambda x: x[1],
        reverse=True,
    )

    return {"top_vibes": sorted_vibes[:5], "counts": dict(counts)}


def download_photos(photos: list[dict], restaurant_name: str) -> list[str]:
    """Download photos to local directory."""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    safe_name = "".join(
        c if c.isalnum() or c in " -_" else "_" for c in restaurant_name
    )
    safe_name = safe_name.replace(" ", "_")[:30]

    downloaded = []

    for i, photo in enumerate(photos[:IMAGES_NEEDED]):
        url = photo.get("url")
        if not url:
            continue

        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                filename = f"{safe_name}_vibe_{i+1}.jpg"
                filepath = IMAGES_DIR / filename
                with open(filepath, "wb") as f:
                    f.write(response.content)
                downloaded.append(filename)
        except Exception as e:
            print(f"      ⚠️ Download failed: {e}")

    return downloaded


# ==============================================================================
# MAIN PIPELINE
# ==============================================================================


def process_restaurant(client: ApiClient, query: str) -> dict | None:
    """Process a single restaurant. Returns None if requirements not met."""

    print(f"\n{'='*50}")
    print(f"🍽️  {query}")
    print(f"{'='*50}")

    # Step 1: Get restaurant info
    print("  🔍 Searching...")
    info = get_restaurant_data(client, query)

    if not info:
        print("  ❌ SKIP: Restaurant not found")
        return None

    print(f"  ✅ Found: {info['name']}")
    print(f"     Google ID: {info['google_id']}")

    if not info.get("google_id"):
        print("  ❌ SKIP: No google_id (can't fetch photos)")
        return None

    # Step 2: Get vibe photos via SerpApi
    print("  📷 Fetching vibe photos...")
    vibe_photos = get_vibe_photos_serpapi(info["google_id"], limit=IMAGES_NEEDED)

    if len(vibe_photos) < IMAGES_NEEDED:
        print(f"  ❌ SKIP: Only {len(vibe_photos)} vibe photos (need {IMAGES_NEEDED})")
        return None

    print(f"  ✅ Got {len(vibe_photos)} vibe photos")

    # Step 3: Get reviews
    print(f"  📝 Fetching {REVIEWS_NEEDED} reviews...")
    reviews = get_reviews(client, info["place_id"], REVIEWS_NEEDED)

    if len(reviews) < REVIEWS_NEEDED:
        print(f"  ❌ SKIP: Only {len(reviews)} reviews (need {REVIEWS_NEEDED})")
        return None

    print(f"  ✅ Got {len(reviews)} reviews")

    # Step 4: Analyze vibes
    vibe_analysis = analyze_vibes(reviews)

    # Step 5: Download photos
    print("  💾 Downloading photos...")
    downloaded = download_photos(vibe_photos, info["name"])
    print(f"  ✅ Downloaded {len(downloaded)} photos")

    return {
        "info": info,
        "vibe_photos": [p["url"] for p in vibe_photos[:IMAGES_NEEDED]],
        "downloaded_files": downloaded,
        "reviews": [
            {"text": r.get("review_text", "")[:300], "likes": r.get("review_likes", 0)}
            for r in reviews
        ],
        "vibe_analysis": vibe_analysis,
    }


def main():
    print("\n" + "=" * 50)
    print("🎯 VIBECHECK: SERPAPI VIBE PHOTOS TEST")
    print("=" * 50)

    # Check API keys
    if not OUTSCRAPER_API_KEY:
        print("\n❌ Set OUTSCRAPER_API_KEY environment variable")
        return

    if not SERPAPI_API_KEY:
        print("\n❌ Set SERPAPI_API_KEY environment variable")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load checkpoint
    checkpoint = load_checkpoint()
    already_processed = set(checkpoint["processed"])

    print(f"\n📋 Total restaurants: {len(TEST_RESTAURANTS)}")
    print(f"✅ Already processed: {len(already_processed)}")
    print(f"⏳ Remaining: {len(TEST_RESTAURANTS) - len(already_processed)}")
    print(f"Requirements: {IMAGES_NEEDED} vibe photos, {REVIEWS_NEEDED} reviews")

    # Check if already done
    if len(already_processed) >= len(TEST_RESTAURANTS):
        print("\n🎉 All restaurants already processed!")
        print(f"📁 Results: {OUTPUT_DIR / 'vibecheck_results.json'}")
        return

    client = ApiClient(api_key=OUTSCRAPER_API_KEY)

    # Track SerpApi calls this session
    serpapi_calls = 0
    SERPAPI_LIMIT = 250  # Free tier limit

    # Process restaurants
    for query in TEST_RESTAURANTS:
        # Skip if already processed
        if query in already_processed:
            continue

        # Check SerpApi budget
        if serpapi_calls >= SERPAPI_LIMIT:
            print(f"\n⚠️  SerpApi limit reached ({SERPAPI_LIMIT} calls)")
            print("    Switch to a teammate's API key and re-run!")
            break

        result = process_restaurant(client, query)
        serpapi_calls += 1  # Each restaurant = 1 SerpApi call

        # Update checkpoint
        checkpoint["processed"].append(query)
        if result:
            checkpoint["results"].append(result)
        else:
            checkpoint["skipped"].append(query)

        save_checkpoint(checkpoint)

        print(
            f"    💾 Checkpoint saved ({len(checkpoint['processed'])}/{len(TEST_RESTAURANTS)})"
        )

    # Save final results
    output_file = OUTPUT_DIR / "vibecheck_results.json"
    with open(output_file, "w") as f:
        json.dump(checkpoint["results"], f, indent=2, default=str)

    # Summary
    print(f"\n{'='*50}")
    print("📊 SUMMARY")
    print(f"{'='*50}")
    print(f"📍 This session: {serpapi_calls} SerpApi calls")
    print(f"✅ Total passed: {len(checkpoint['results'])}/{len(TEST_RESTAURANTS)}")
    print(f"❌ Total skipped: {len(checkpoint['skipped'])}")
    print(f"⏳ Remaining: {len(TEST_RESTAURANTS) - len(checkpoint['processed'])}")

    if checkpoint["skipped"]:
        print("\nSkipped restaurants:")
        for s in checkpoint["skipped"]:
            print(f"   - {s}")

    print(f"\n📁 Results: {output_file}")
    print(f"📷 Images: {IMAGES_DIR}")
    print(f"💾 Checkpoint: {CHECKPOINT_FILE}")


if __name__ == "__main__":
    main()
