"""
VibeCheck: FULL DC Restaurant Scraper
======================================
Fetches ALL DC restaurants, then pulls vibe photos + reviews for each.
Automatically resumes from checkpoint if API limit is hit.

Usage:
    1. Set your API keys (environment variables or edit below)
    2. Run: python vibecheck_full_dc.py
    3. If API runs out, update the key and re-run — it will resume automatically
"""

import json
import os
import re
import time
from collections import defaultdict
from pathlib import Path

import requests
from outscraper import ApiClient

# ==============================================================================
# CONFIG - UPDATE YOUR API KEYS HERE
# ==============================================================================

OUTSCRAPER_API_KEY = os.getenv(
    "OUTSCRAPER_API_KEY", "NDA1NWE2OTY1YzJkNDE1MDljM2MyMDVkZGY3NGQ4MjJ8YWE3OTNhM2I4Zg"
)
SERPAPI_API_KEY = os.getenv(
    "SERPAPI_API_KEY", "dc23befcdf07f4ca7d5fcb6af5e76a2fcf0384473e88be3dee29723d4e9c24c1"
)

# Google Maps photo category IDs
VIBE_CATEGORY_ID = "CgIYIg=="  # Interior/Atmosphere photos

# Requirements per restaurant
REVIEWS_NEEDED = 5
IMAGES_NEEDED = 5

# Output paths
OUTPUT_DIR = Path("./vibecheck_full_output")
IMAGES_DIR = OUTPUT_DIR / "images"
CHECKPOINT_FILE = OUTPUT_DIR / "checkpoint.json"
RESTAURANTS_FILE = OUTPUT_DIR / "all_restaurants.json"

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
# FETCH ALL DC RESTAURANTS (BY NEIGHBORHOOD)
# ==============================================================================


def get_all_dc_restaurants(client: ApiClient, limit: int = 500) -> list[dict]:
    """Fetch DC restaurants using multiple neighborhood searches."""
    print(f"\n{'='*50}")
    print(f"🔍 FETCHING DC RESTAURANTS BY NEIGHBORHOOD")
    print(f"{'='*50}")

    SEARCH_QUERIES = [
        "restaurants in Washington DC",
        "restaurants in Georgetown DC",
        "restaurants in Dupont Circle DC",
        "restaurants in Adams Morgan DC",
        "restaurants in Capitol Hill DC",
        "restaurants in U Street DC",
        "restaurants in Navy Yard DC",
        "restaurants in Foggy Bottom DC",
        "restaurants in Columbia Heights DC",
        "restaurants in Shaw DC",
        "restaurants in Logan Circle DC",
        "restaurants in Chinatown DC",
        "restaurants in Penn Quarter DC",
        "restaurants in NoMa DC",
        "restaurants in Petworth DC",
        "restaurants in Brookland DC",
        "restaurants in Cleveland Park DC",
        "restaurants in Woodley Park DC",
        "restaurants in Glover Park DC",
        "restaurants in Tenleytown DC",
    ]

    all_restaurants = {}  # Dict to dedupe by place_id

    for query in SEARCH_QUERIES:
        print(f"  🔍 Searching: {query}")
        try:
            results = client.google_maps_search(
                query,
                limit=100,
                language="en",
                region="us"
            )

            if results:
                places = results[0] if isinstance(results[0], list) else results
                for place in places:
                    place_id = place.get("place_id")
                    name = place.get("name")
                    if place_id and name and place_id not in all_restaurants:
                        all_restaurants[place_id] = {
                            "query": f"{name} Washington DC",
                            "name": name,
                            "place_id": place_id,
                            "google_id": place.get("google_id"),
                            "address": place.get("full_address") or place.get("address"),
                            "rating": place.get("rating"),
                            "reviews_count": place.get("reviews"),
                        }
                print(f"     ✅ Found {len(places)} (total unique: {len(all_restaurants)})")
        except Exception as e:
            print(f"     ❌ Error: {e}")

        time.sleep(1)  # Be nice to API

    restaurants = list(all_restaurants.values())
    print(f"\n✅ Total unique restaurants: {len(restaurants)}")
    return restaurants


# ==============================================================================
# SERPAPI: Fetch vibe photos
# ==============================================================================


def get_vibe_photos_serpapi(google_id: str, limit: int = 10) -> list[dict]:
    """Fetch VIBE-category photos from Google Maps via SerpApi."""
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
    """Fetch reviews sorted by relevance."""
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

    safe_name = "".join(c if c.isalnum() or c in " -" else "" for c in restaurant_name)
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
# PROCESS ONE RESTAURANT
# ==============================================================================


def process_restaurant(client: ApiClient, restaurant: dict) -> dict | None:
    """Process a single restaurant. Returns None if requirements not met."""

    query = restaurant.get("query") or restaurant.get("name")

    print(f"\n{'='*50}")
    print(f"🍽️  {query}")
    print(f"{'='*50}")

    # Step 1: Get restaurant info (use cached data if available)
    if restaurant.get("google_id"):
        info = restaurant
        print(f"  ✅ Using cached info: {info['name']}")
        print(f"     Google ID: {info['google_id']}")
    else:
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
        "info": {
            "name": info.get("name"),
            "place_id": info.get("place_id"),
            "google_id": info.get("google_id"),
            "address": info.get("address"),
            "rating": info.get("rating"),
            "reviews_count": info.get("reviews_count"),
        },
        "vibe_photos": [p["url"] for p in vibe_photos[:IMAGES_NEEDED]],
        "downloaded_files": downloaded,
        "reviews": [
            {"text": r.get("review_text", "")[:300], "likes": r.get("review_likes", 0)}
            for r in reviews
        ],
        "vibe_analysis": vibe_analysis,
    }


# ==============================================================================
# MAIN PIPELINE
# ==============================================================================


def main():
    print("\n" + "=" * 60)
    print("🎯 VIBECHECK: FULL DC RESTAURANT SCRAPER")
    print("=" * 60)

    # Check API keys
    if OUTSCRAPER_API_KEY == "YOUR_KEY_HERE" or not OUTSCRAPER_API_KEY:
        print("\n❌ Set OUTSCRAPER_API_KEY at the top of the script or as environment variable")
        return

    if SERPAPI_API_KEY == "YOUR_KEY_HERE" or not SERPAPI_API_KEY:
        print("\n❌ Set SERPAPI_API_KEY at the top of the script or as environment variable")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    client = ApiClient(api_key=OUTSCRAPER_API_KEY)

    # -------------------------------------------------------------------------
    # Step 1: Get all DC restaurants (cached after first run)
    # -------------------------------------------------------------------------
    if RESTAURANTS_FILE.exists():
        with open(RESTAURANTS_FILE) as f:
            all_restaurants = json.load(f)
        print(f"\n📋 Loaded {len(all_restaurants)} restaurants from cache")
        print(f"   (Delete {RESTAURANTS_FILE} to fetch fresh list)")
    else:
        all_restaurants = get_all_dc_restaurants(client)
        if not all_restaurants:
            print("❌ Failed to fetch restaurant list. Check your Outscraper API key.")
            return
        with open(RESTAURANTS_FILE, "w") as f:
            json.dump(all_restaurants, f, indent=2)
        print(f"💾 Saved restaurant list to {RESTAURANTS_FILE}")

    # -------------------------------------------------------------------------
    # Step 2: Load checkpoint and show progress
    # -------------------------------------------------------------------------
    checkpoint = load_checkpoint()
    already_processed = set(checkpoint["processed"])

    remaining = [r for r in all_restaurants if r.get("query", r.get("name")) not in already_processed]

    print(f"\n📊 PROGRESS")
    print(f"   Total restaurants: {len(all_restaurants)}")
    print(f"   Already processed: {len(already_processed)}")
    print(f"   Successful: {len(checkpoint['results'])}")
    print(f"   Skipped: {len(checkpoint['skipped'])}")
    print(f"   Remaining: {len(remaining)}")
    print(f"\nRequirements: {IMAGES_NEEDED} vibe photos, {REVIEWS_NEEDED} reviews per restaurant")

    if not remaining:
        print("\n🎉 All restaurants already processed!")
        print(f"📁 Results: {OUTPUT_DIR / 'vibecheck_results.json'}")
        return

    input(f"\n⏳ Press Enter to start processing {len(remaining)} restaurants (Ctrl+C to cancel)...")

    # -------------------------------------------------------------------------
    # Step 3: Process each restaurant
    # -------------------------------------------------------------------------
    serpapi_calls = 0
    api_errors_in_a_row = 0
    MAX_CONSECUTIVE_ERRORS = 5  # Stop if we hit 5 API errors in a row

    for i, restaurant in enumerate(remaining):
        query = restaurant.get("query") or restaurant.get("name")

        # Check for too many consecutive errors (likely API limit hit)
        if api_errors_in_a_row >= MAX_CONSECUTIVE_ERRORS:
            print(f"\n⚠️  Hit {MAX_CONSECUTIVE_ERRORS} API errors in a row.")
            print("    Likely hit API limit. Update your API key and re-run!")
            break

        try:
            result = process_restaurant(client, restaurant)
            serpapi_calls += 1
            api_errors_in_a_row = 0  # Reset on success

            # Update checkpoint
            checkpoint["processed"].append(query)
            if result:
                checkpoint["results"].append(result)
            else:
                checkpoint["skipped"].append(query)

            save_checkpoint(checkpoint)

            progress = len(checkpoint["processed"])
            total = len(all_restaurants)
            success = len(checkpoint["results"])
            print(f"    💾 Checkpoint saved ({progress}/{total}) | ✅ {success} successful")

            # Small delay to be nice to APIs
            time.sleep(0.5)

        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user. Progress saved!")
            break
        except Exception as e:
            error_msg = str(e).lower()
            if "api" in error_msg or "limit" in error_msg or "quota" in error_msg or "unauthorized" in error_msg:
                api_errors_in_a_row += 1
                print(f"    ⚠️  API error ({api_errors_in_a_row}/{MAX_CONSECUTIVE_ERRORS}): {e}")
            else:
                print(f"    ❌ Unexpected error: {e}")
                checkpoint["processed"].append(query)
                checkpoint["skipped"].append(query)
                save_checkpoint(checkpoint)

    # -------------------------------------------------------------------------
    # Step 4: Save final results and show summary
    # -------------------------------------------------------------------------
    output_file = OUTPUT_DIR / "vibecheck_results.json"
    with open(output_file, "w") as f:
        json.dump(checkpoint["results"], f, indent=2, default=str)

    print(f"\n{'='*60}")
    print("📊 FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"📍 SerpApi calls this session: {serpapi_calls}")
    print(f"✅ Total successful: {len(checkpoint['results'])}/{len(all_restaurants)}")
    print(f"❌ Total skipped: {len(checkpoint['skipped'])}")
    print(f"⏳ Remaining: {len(all_restaurants) - len(checkpoint['processed'])}")

    print(f"\n📁 Results: {output_file}")
    print(f"📷 Images: {IMAGES_DIR}")
    print(f"💾 Checkpoint: {CHECKPOINT_FILE}")

    if len(all_restaurants) - len(checkpoint["processed"]) > 0:
        print(f"\n💡 To continue: Update API key if needed, then run this script again.")


if __name__ == "__main__":
    main()

