"""
VibeCheck: FULL DC Restaurant Scraper (SerpAPI Only) - FIXED v3
================================================================
Fetches ALL DC restaurants using ONLY SerpAPI (no Outscraper needed).
Automatically resumes from checkpoint if API limit is hit.

FIX: Uses place_id to get full details including data_id

Usage:
    1. Set your SERPAPI_API_KEY below
    2. Delete vibecheck_full_output/checkpoint.json to start fresh
    3. Run: python vibecheck_full_dc.py
    4. If API runs out, update the key and re-run — it will resume automatically
"""

import json
import os
import re
import time
from collections import defaultdict
from pathlib import Path

import requests

# ==============================================================================
# CONFIG - UPDATE YOUR API KEY HERE
# ==============================================================================

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
# SERPAPI: Get place details using place_id
# ==============================================================================


def get_place_details(place_id: str) -> dict | None:
    """
    Get full place details including data_id using place_id.
    This uses the 'place' type search which returns complete info.
    """
    url = "https://serpapi.com/search.json"
    
    params = {
        "engine": "google_maps",
        "type": "place",
        "place_id": place_id,
        "hl": "en",
        "api_key": SERPAPI_API_KEY,
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()

        if "error" in data:
            print(f"      API Error: {data['error']}")
            return None

        # The place details are in the 'place_results' key
        place_results = data.get("place_results", {})
        
        if not place_results:
            return None
        
        return {
            "data_id": place_results.get("data_id"),
            "name": place_results.get("title"),
            "rating": place_results.get("rating"),
            "reviews_count": place_results.get("reviews"),
            "address": place_results.get("address"),
        }

    except Exception as e:
        print(f"      Error getting place details: {e}")
        return None


# ==============================================================================
# SERPAPI: Fetch restaurants by neighborhood
# ==============================================================================


def search_restaurants_serpapi(query: str, limit: int = 100) -> list[dict]:
    """Search for restaurants using SerpAPI Google Maps."""
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_maps",
        "q": query,
        "type": "search",
        "hl": "en",
        "api_key": SERPAPI_API_KEY,
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()

        if "error" in data:
            print(f"      ❌ SerpApi error: {data['error']}")
            return []

        restaurants = []
        for place in data.get("local_results", [])[:limit]:
            restaurants.append({
                "name": place.get("title"),
                "place_id": place.get("place_id"),
                "data_id": place.get("data_id"),  # May be None
                "address": place.get("address"),
                "rating": place.get("rating"),
                "reviews_count": place.get("reviews"),
                "gps_coordinates": place.get("gps_coordinates"),
            })

        return restaurants

    except Exception as e:
        print(f"      ❌ SerpApi search error: {e}")
        return []


def get_all_dc_restaurants() -> list[dict]:
    """Fetch DC restaurants using multiple neighborhood searches via SerpAPI."""
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
            places = search_restaurants_serpapi(query, limit=100)

            for place in places:
                place_id = place.get("place_id")
                name = place.get("name")
                
                if place_id and name and place_id not in all_restaurants:
                    all_restaurants[place_id] = {
                        "query": f"{name} Washington DC",
                        "name": name,
                        "place_id": place_id,
                        "data_id": place.get("data_id"),  # Store even if None
                        "address": place.get("address"),
                        "rating": place.get("rating"),
                        "reviews_count": place.get("reviews_count"),
                    }
            print(f"     ✅ Found {len(places)} (total unique: {len(all_restaurants)})")
        except Exception as e:
            print(f"     ❌ Error: {e}")

        time.sleep(1)  # Be nice to API

    restaurants = list(all_restaurants.values())
    print(f"\n✅ Total unique restaurants: {len(restaurants)}")
    
    # Count how many are missing data_id
    missing_data_id = sum(1 for r in restaurants if not r.get("data_id"))
    if missing_data_id > 0:
        print(f"⚠️  {missing_data_id} restaurants missing data_id (will fetch during processing)")
    
    return restaurants


# ==============================================================================
# SERPAPI: Fetch vibe photos
# ==============================================================================


def get_vibe_photos_serpapi(data_id: str, limit: int = 10) -> list[dict]:
    """Fetch VIBE-category photos from Google Maps via SerpApi."""
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_maps_photos",
        "data_id": data_id,
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
            photos.append({
                "url": photo.get("image"),
                "thumbnail": photo.get("thumbnail"),
            })

        return photos

    except Exception as e:
        print(f"      ❌ SerpApi photos error: {e}")
        return []


# ==============================================================================
# SERPAPI: Fetch reviews
# ==============================================================================


def get_reviews_serpapi(data_id: str, limit: int = 5) -> list[dict]:
    """Fetch reviews from Google Maps via SerpApi."""
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_maps_reviews",
        "data_id": data_id,
        "hl": "en",
        "sort_by": "qualityScore",  # Most relevant
        "api_key": SERPAPI_API_KEY,
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()

        if "error" in data:
            print(f"      ❌ SerpApi error: {data['error']}")
            return []

        reviews = []
        for review in data.get("reviews", [])[:limit]:
            reviews.append({
                "review_text": review.get("snippet") or review.get("extracted_snippet", {}).get("original"),
                "rating": review.get("rating"),
                "date": review.get("date"),
                "likes": review.get("likes", 0),
            })

        return reviews

    except Exception as e:
        print(f"      ❌ SerpApi reviews error: {e}")
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


def process_restaurant(restaurant: dict) -> dict | None:
    """Process a single restaurant. Returns None if requirements not met."""

    query = restaurant.get("query") or restaurant.get("name")

    print(f"\n{'='*50}")
    print(f"🍽️  {query}")
    print(f"{'='*50}")

    data_id = restaurant.get("data_id")

    # If no data_id, fetch full place details using place_id
    if not data_id:
        place_id = restaurant.get("place_id")
        if not place_id:
            print("  ❌ SKIP: No place_id available")
            return None
            
        print("  🔍 Missing data_id, fetching place details...")
        place_details = get_place_details(place_id)
        time.sleep(0.5)  # Small delay after lookup
        
        if not place_details or not place_details.get("data_id"):
            print("  ❌ SKIP: Could not retrieve data_id from place details")
            return None
        
        data_id = place_details["data_id"]
        print(f"  ✅ Got data_id: {data_id}")
        
        # Update restaurant record with any new info
        restaurant["data_id"] = data_id
        if place_details.get("rating"):
            restaurant["rating"] = place_details["rating"]
        if place_details.get("reviews_count"):
            restaurant["reviews_count"] = place_details["reviews_count"]

    print(f"  ✅ Restaurant: {restaurant['name']}")
    print(f"     Data ID: {data_id}")

    # Step 1: Get vibe photos via SerpApi
    print("  📷 Fetching vibe photos...")
    vibe_photos = get_vibe_photos_serpapi(data_id, limit=IMAGES_NEEDED)

    if len(vibe_photos) < IMAGES_NEEDED:
        print(f"  ❌ SKIP: Only {len(vibe_photos)} vibe photos (need {IMAGES_NEEDED})")
        return None

    print(f"  ✅ Got {len(vibe_photos)} vibe photos")

    # Step 2: Get reviews via SerpApi
    print(f"  📝 Fetching {REVIEWS_NEEDED} reviews...")
    reviews = get_reviews_serpapi(data_id, REVIEWS_NEEDED)

    if len(reviews) < REVIEWS_NEEDED:
        print(f"  ❌ SKIP: Only {len(reviews)} reviews (need {REVIEWS_NEEDED})")
        return None

    print(f"  ✅ Got {len(reviews)} reviews")

    # Step 3: Analyze vibes
    vibe_analysis = analyze_vibes(reviews)

    # Step 4: Download photos
    print("  💾 Downloading photos...")
    downloaded = download_photos(vibe_photos, restaurant["name"])
    print(f"  ✅ Downloaded {len(downloaded)} photos")

    return {
        "info": {
            "name": restaurant.get("name"),
            "place_id": restaurant.get("place_id"),
            "data_id": data_id,
            "address": restaurant.get("address"),
            "rating": restaurant.get("rating"),
            "reviews_count": restaurant.get("reviews_count"),
        },
        "vibe_photos": [p["url"] for p in vibe_photos[:IMAGES_NEEDED]],
        "downloaded_files": downloaded,
        "reviews": [
            {"text": r.get("review_text", "")[:300] if r.get("review_text") else "", "likes": r.get("likes", 0)}
            for r in reviews
        ],
        "vibe_analysis": vibe_analysis,
    }


# ==============================================================================
# MAIN PIPELINE
# ==============================================================================


def main():
    print("\n" + "=" * 60)
    print("🎯 VIBECHECK: FULL DC RESTAURANT SCRAPER (SerpAPI Only)")
    print("=" * 60)

    # Check API key
    if SERPAPI_API_KEY == "YOUR_KEY_HERE" or not SERPAPI_API_KEY:
        print("\n❌ Set SERPAPI_API_KEY at the top of the script or as environment variable")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # Step 1: Get all DC restaurants (cached after first run)
    # -------------------------------------------------------------------------
    if RESTAURANTS_FILE.exists():
        with open(RESTAURANTS_FILE) as f:
            all_restaurants = json.load(f)
        print(f"\n📋 Loaded {len(all_restaurants)} restaurants from cache")
        print(f"   (Delete {RESTAURANTS_FILE} to fetch fresh list)")
    else:
        all_restaurants = get_all_dc_restaurants()
        if not all_restaurants:
            print("❌ Failed to fetch restaurant list. Check your SerpAPI key.")
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
    print(f"\n⚠️  Each restaurant uses ~3 SerpAPI calls (1 for place details + 1 photos + 1 reviews)")

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
            had_data_id = bool(restaurant.get("data_id"))
            result = process_restaurant(restaurant)
            
            # Count API calls (3 if we had to fetch place details, 2 otherwise)
            if not had_data_id:
                serpapi_calls += 3
            else:
                serpapi_calls += 2
                
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
            print(f"    💾 Checkpoint saved ({progress}/{total}) | ✅ {success} successful | 🔍 {serpapi_calls} API calls")

            # Small delay to be nice to API
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
            
            # Still save to checkpoint even on error
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