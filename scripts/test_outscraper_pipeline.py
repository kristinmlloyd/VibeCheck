"""
Test script for Outscraper + Vibe Analysis
==========================================
Tests the pipeline with just 2 restaurants: Le Diplomate and Bar Chinois

Usage:
    cd VibeCheck-git
    python scripts/test_outscraper_pipeline.py

Requirements:
    pip install outscraper requests
"""

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import requests

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from outscraper import ApiClient

# ==============================================================================
# CONFIG
# ==============================================================================

OUTSCRAPER_API_KEY = os.getenv("OUTSCRAPER_API_KEY", "your_outscraper_key_here")

# Test restaurants
TEST_RESTAURANTS = [
    "Le Diplomate Washington DC",
    "Bar Chinois Washington DC",
]

# Limits for testing
REVIEWS_LIMIT = 30
PHOTOS_LIMIT = 10

# Output paths (relative to project root)
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "test_output"
IMAGES_DIR = PROJECT_ROOT / "data" / "images" / "restaurant_images"

# ==============================================================================
# VIBE ANALYZER (inline for easy testing)
# ==============================================================================

VIBE_PATTERNS = {
    "dim_lighting": {
        "display_name": "Dim/Romantic Lighting",
        "patterns": [
            r"\bdim(ly)?\s*(lit|lighting|lights?)?\b",
            r"\bcandle\s*lit\b",
            r"\bcandlelit\b",
            r"\bcandles\b",
            r"\blow\s*light(ing|s)?\b",
            r"\bsoft\s*light(ing|s)?\b",
            r"\bmoody\s*light(ing)?\b",
            r"\bdark(er|ened|ish)?\s*(inside|interior)?\b",
            r"\bwarm\s*glow\b",
            r"\bambient\s*light(ing)?\b",
        ],
    },
    "bright_lighting": {
        "display_name": "Bright/Well-Lit",
        "patterns": [
            r"\bbright(ly)?\s*(lit|lighting)?\b",
            r"\bwell[\s-]*lit\b",
            r"\bnatural\s*light\b",
            r"\bsunny\b",
            r"\bopen\s*and\s*airy\b",
        ],
    },
    "loud_noisy": {
        "display_name": "Loud/Noisy",
        "patterns": [
            r"\bloud\b",
            r"\bnoisy\b",
            r"\bcouldn'?t\s*hear\b",
            r"\bhard\s*to\s*(hear|talk)\b",
            r"\bbustling\b",
        ],
    },
    "quiet_intimate": {
        "display_name": "Quiet/Good for Conversation",
        "patterns": [
            r"\bquiet\b",
            r"\bpeaceful\b",
            r"\bcalm\b",
            r"\bintimate\b",
            r"\beasy\s*to\s*(talk|converse|hear)\b",
            r"\bnot\s*(too\s*)?(loud|noisy)\b",
        ],
    },
    "lively_energetic": {
        "display_name": "Lively/High Energy",
        "patterns": [
            r"\blively\b",
            r"\benergetic\b",
            r"\bbuzzy?\b",
            r"\bvibrant\b",
            r"\bhigh[\s-]*energy\b",
            r"\bscene\b",
            r"\bhopping\b",
        ],
    },
    "chill_relaxed": {
        "display_name": "Chill/Relaxed",
        "patterns": [
            r"\bchill\b",
            r"\blaid[\s-]*back\b",
            r"\brelax(ed|ing)\b",
            r"\blow[\s-]*key\b",
            r"\bcozy\b",
            r"\bcomfort(able)?\b",
        ],
    },
    "upscale_fancy": {
        "display_name": "Upscale/Fancy",
        "patterns": [
            r"\bupscale\b",
            r"\bfancy\b",
            r"\belegant\b",
            r"\bsophisticated\b",
            r"\bclassy\b",
            r"\bchic\b",
            r"\bluxur(y|ious)\b",
            r"\bfine\s*dining\b",
        ],
    },
    "casual_divey": {
        "display_name": "Casual/Divey",
        "patterns": [
            r"\bcasual\b",
            r"\bdivey?\b",
            r"\bhole[\s-]*in[\s-]*the[\s-]*wall\b",
            r"\bno[\s-]*frills\b",
            r"\bneighborhood\s*(spot|gem|joint)\b",
        ],
    },
    "romantic_date": {
        "display_name": "Romantic/Date Night",
        "patterns": [
            r"\bromantic\b",
            r"\bdate\s*(night|spot)?\b",
            r"\banniversary\b",
            r"\bspecial\s*occasion\b",
            r"\bperfect\s*for\s*(a\s*)?(date|couples?)\b",
        ],
    },
    "spacious_open": {
        "display_name": "Spacious/Open",
        "patterns": [
            r"\bspacious\b",
            r"\bopen\b.*\b(space|layout)\b",
            r"\bhigh\s*ceilings?\b",
            r"\broom(y)?\b",
            r"\bnot\s*(too\s*)?cramped\b",
        ],
    },
    "cramped_tight": {
        "display_name": "Cramped/Tight",
        "patterns": [
            r"\bcramped\b",
            r"\btight\b.*\b(space|seating)\b",
            r"\bsqueez(ed|y)\b",
            r"\bsmall\b.*\b(space|tables?)\b",
            r"\belbow\s*to\s*elbow\b",
        ],
    },
    "modern_trendy": {
        "display_name": "Modern/Trendy",
        "patterns": [
            r"\bmodern\b",
            r"\btrendy\b",
            r"\bstylish\b",
            r"\bcontemporary\b",
            r"\binstagram(mable)?\b",
            r"\bhip(ster)?\b",
            r"\bphotogenic\b",
        ],
    },
    "outdoor_seating": {
        "display_name": "Outdoor Seating/Patio",
        "patterns": [
            r"\boutdoor\s*(seating|patio|area)?\b",
            r"\bpatio\b",
            r"\brooftop\b",
            r"\bterrace\b",
            r"\bal\s*fresco\b",
            r"\bsidewalk\b",
        ],
    },
    "bar_scene": {
        "display_name": "Great Bar/Drinks Scene",
        "patterns": [
            r"\bbar\s*(scene|area)?\b",
            r"\bcocktail(s)?\b",
            r"\bhappy\s*hour\b",
            r"\bwine\s*(list|selection)\b",
            r"\bcraft\s*(beer|cocktail)s?\b",
        ],
    },
}


def analyze_vibes(reviews: list[dict], restaurant_name: str) -> dict:
    """Analyze reviews for vibe mentions."""

    # Compile patterns
    compiled = {
        cat: [re.compile(p, re.IGNORECASE) for p in cfg["patterns"]]
        for cat, cfg in VIBE_PATTERNS.items()
    }

    mention_counts = defaultdict(int)
    mention_examples = defaultdict(list)

    for review in reviews:
        text = review.get("review_text", "") or ""
        likes = review.get("review_likes") or 0

        for category, patterns in compiled.items():
            for pattern in patterns:
                if pattern.search(text):
                    mention_counts[category] += 1
                    if len(mention_examples[category]) < 3:
                        mention_examples[category].append(
                            {
                                "text": text[:200],
                                "likes": likes,
                            }
                        )
                    break  # Count each category once per review

    # Sort by count
    sorted_vibes = sorted(
        [
            (VIBE_PATTERNS[cat]["display_name"], count)
            for cat, count in mention_counts.items()
        ],
        key=lambda x: x[1],
        reverse=True,
    )

    return {
        "restaurant": restaurant_name,
        "reviews_analyzed": len(reviews),
        "vibe_counts": {
            VIBE_PATTERNS[cat]["display_name"]: count
            for cat, count in mention_counts.items()
        },
        "top_vibes": sorted_vibes[:10],
        "examples": {
            VIBE_PATTERNS[cat]["display_name"]: examples
            for cat, examples in mention_examples.items()
        },
    }


# ==============================================================================
# OUTSCRAPER FUNCTIONS
# ==============================================================================


def get_restaurant_data(client: ApiClient, query: str) -> dict:
    """Search for a restaurant and get basic info."""
    print(f"  🔍 Searching for: {query}")

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
                    "photos_count": place.get("photos_count"),
                    "type": place.get("type"),
                    "subtypes": place.get("subtypes"),
                    "phone": place.get("phone"),
                    "website": place.get("site"),
                    "latitude": place.get("latitude"),
                    "longitude": place.get("longitude"),
                }
    except Exception as e:
        print(f"  ❌ Error searching: {e}")

    return None


def get_reviews(client: ApiClient, place_id: str, limit: int = 30) -> list[dict]:
    """Fetch reviews for a restaurant."""
    print(f"  📝 Fetching {limit} reviews...")

    try:
        results = client.google_maps_reviews(
            [place_id],
            reviews_limit=limit,
            language="en",
            sort="most_relevant",  # Gets popular/helpful reviews
        )

        if results and len(results) > 0:
            place_data = results[0]
            reviews = place_data.get("reviews_data", [])

            # Sort by likes
            reviews = sorted(
                reviews, key=lambda x: x.get("review_likes") or 0, reverse=True
            )

            return reviews

    except Exception as e:
        print(f"  ❌ Error fetching reviews: {e}")

    return []


def get_photos(client: ApiClient, place_id: str, limit: int = 10) -> list[dict]:
    """Fetch photos for a restaurant."""
    print(f"  📷 Fetching {limit} photos...")

    try:
        results = client.google_maps_photos(
            [place_id], photosLimit=limit, language="en"
        )

        if results and len(results) > 0:
            place_data = results[0]
            # Handle different response formats
            if isinstance(place_data, dict):
                return place_data.get("photos", [])
            elif isinstance(place_data, list):
                # Sometimes returns list of photo objects directly
                return place_data

    except Exception as e:
        print(f"  ❌ Error fetching photos: {e}")

    return []


def download_photos(
    photos: list[dict], restaurant_name: str, output_dir: Path
) -> list[str]:
    """Download photos to local directory."""
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_name = "".join(
        c if c.isalnum() or c in " -_" else "_" for c in restaurant_name
    )
    safe_name = safe_name.replace(" ", "_")[:30]

    downloaded = []

    for i, photo in enumerate(photos):
        url = photo.get("photo_url") or photo.get("original")
        if not url:
            continue

        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                filename = f"{safe_name}_outscraper_{i+1}.jpg"
                filepath = output_dir / filename
                with open(filepath, "wb") as f:
                    f.write(response.content)
                downloaded.append(filename)
                print(f"    ✅ Downloaded: {filename}")
        except Exception as e:
            print(f"    ⚠️ Failed to download photo {i+1}: {e}")

    return downloaded


# ==============================================================================
# MAIN TEST
# ==============================================================================


def test_restaurant(client: ApiClient, query: str) -> dict:
    """Run full test on a single restaurant."""

    print(f"\n{'='*60}")
    print(f"🍽️  Testing: {query}")
    print(f"{'='*60}")

    # Step 1: Get basic info
    info = get_restaurant_data(client, query)
    if not info:
        print("  ❌ Restaurant not found!")
        return None

    print(f"  ✅ Found: {info['name']}")
    print(f"     Rating: {info['rating']} ⭐ ({info['reviews_count']} reviews)")
    print(f"     Address: {info['address']}")

    place_id = info["place_id"]

    # Step 2: Get reviews
    reviews = get_reviews(client, place_id, REVIEWS_LIMIT)
    print(f"  ✅ Got {len(reviews)} reviews")

    # Show top reviews by engagement
    high_engagement = [r for r in reviews if (r.get("review_likes") or 0) >= 3]
    print(f"     High engagement reviews (3+ likes): {len(high_engagement)}")

    if reviews:
        top_review = reviews[0]
        print(f"\n  📈 Top review ({top_review.get('review_likes', 0)} likes):")
        print(f"     \"{(top_review.get('review_text') or '')[:150]}...\"")

    # Step 3: Analyze vibes
    print("\n  🎭 Analyzing vibes...")
    vibe_analysis = analyze_vibes(reviews, info["name"])

    print("\n  📊 VIBE BREAKDOWN:")
    for vibe_name, count in vibe_analysis["top_vibes"][:8]:
        pct = (count / len(reviews)) * 100 if reviews else 0
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"     {vibe_name:30} {count:3} ({pct:4.1f}%) {bar}")

    # Step 4: Get and download photos
    photos = get_photos(client, place_id, PHOTOS_LIMIT)
    print(f"\n  ✅ Got {len(photos)} photo URLs")

    downloaded = download_photos(photos, info["name"], IMAGES_DIR)
    print(f"  ✅ Downloaded {len(downloaded)} photos to {IMAGES_DIR}")

    # Compile result
    result = {
        "info": info,
        "reviews_collected": len(reviews),
        "high_engagement_reviews": [
            {
                "text": r.get("review_text", "")[:500],
                "rating": r.get("review_rating"),
                "likes": r.get("review_likes") or 0,
            }
            for r in high_engagement[:5]
        ],
        "vibe_analysis": vibe_analysis,
        "photos_downloaded": downloaded,
    }

    return result


def main():
    """Run the test."""

    print("\n" + "=" * 60)
    print("🧪 OUTSCRAPER + VIBE ANALYSIS TEST")
    print("=" * 60)
    print(f"Testing {len(TEST_RESTAURANTS)} restaurants")

    # Check API key
    if OUTSCRAPER_API_KEY == "your_outscraper_key_here":
        print("\n⚠️  Please set your OUTSCRAPER_API_KEY!")
        print("   Export it: export OUTSCRAPER_API_KEY='your_key_here'")
        print("   Or edit this script directly.")
        return

    # Initialize client
    client = ApiClient(api_key=OUTSCRAPER_API_KEY)

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Test each restaurant
    results = []
    for query in TEST_RESTAURANTS:
        result = test_restaurant(client, query)
        if result:
            results.append(result)

    # Save results
    output_file = OUTPUT_DIR / "test_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n{'='*60}")
    print("🎉 TEST COMPLETE")
    print(f"{'='*60}")
    print(f"📁 Results saved to: {output_file}")
    print(f"📷 Photos saved to: {IMAGES_DIR}")

    # Summary comparison
    print("\n📊 COMPARISON:")
    print(f"{'Restaurant':<25} {'Rating':<8} {'Reviews':<10} {'Top Vibe'}")
    print("-" * 70)
    for r in results:
        name = r["info"]["name"][:24]
        rating = r["info"]["rating"]
        reviews = r["reviews_collected"]
        top_vibe = (
            r["vibe_analysis"]["top_vibes"][0][0]
            if r["vibe_analysis"]["top_vibes"]
            else "N/A"
        )
        print(f"{name:<25} {rating:<8} {reviews:<10} {top_vibe}")


if __name__ == "__main__":
    main()
