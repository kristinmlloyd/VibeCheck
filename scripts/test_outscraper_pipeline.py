# """
# VibeCheck: Outscraper + Simple YOLO Plate Filter (v4 - FIXED)
# =============================================================
# - Dynamically identifies DC restaurants via Outscraper
# - Randomly selects 10 restaurants
# - Fetches reviews + photos
# - Filters photos using simplified YOLO (removes only zoomed-in plates)
# - Outputs vibe scores + saved vibe photos

# FIXES:
# - Added debug output to identify API response structure
# - Better exception handling (no longer silent)
# - Checks multiple possible keys for reviews and place_id
# """

# import json
# import os
# import re
# import random
# from collections import defaultdict
# from pathlib import Path
# from io import BytesIO
# import requests

# # ==============================================================================
# # CONFIG
# # ==============================================================================

# OUTSCRAPER_API_KEY = os.getenv("OUTSCRAPER_API_KEY", "NDA1NWE2OTY1YzJkNDE1MDljM2MyMDVkZGY3NGQ4MjJ8YWE3OTNhM2I4Zg")

# REVIEWS_NEEDED = 5
# IMAGES_NEEDED = 5
# PHOTOS_TO_FETCH = 10

# OUTPUT_DIR = Path("./data/outscraper_test/")
# IMAGES_DIR = Path("./data/outscraper_test/images/")

# ZOOM_THRESHOLD = 0.25  # 25%

# # Only real food items from COCO
# FOOD_CLASSES = {46, 47, 48, 49, 50, 51, 52, 53, 54, 55}

# # Toggle debug mode
# DEBUG = True

# _yolo_model = None


# # ==============================================================================
# # DEBUG HELPER
# # ==============================================================================

# def debug_print(msg):
#     """Print only if DEBUG is enabled."""
#     if DEBUG:
#         print(f"    🐛 DEBUG: {msg}")


# # ==============================================================================
# # YOLO LOADING
# # ==============================================================================

# def get_yolo_model():
#     """Lazy-load YOLO."""
#     global _yolo_model
#     if _yolo_model is None:
#         from ultralytics import YOLO
#         print("  📦 Loading YOLO model (first time only)...")
#         _yolo_model = YOLO("yolov8n.pt")
#         print("  ✅ YOLO model loaded")
#     return _yolo_model


# # ==============================================================================
# # SIMPLE YOLO FILTER
# # ==============================================================================

# def is_zoomed_in_food_photo(url: str) -> dict:
#     """
#     Returns:
#         { "is_zoomed": bool, "coverage": float }
#     """
#     model = get_yolo_model()
#     if not model:
#         return {"is_zoomed": False, "coverage": 0.0}

#     try:
#         r = requests.get(url, timeout=10)
#         if r.status_code != 200:
#             return {"is_zoomed": False, "coverage": 0.0}

#         from PIL import Image
#         img = Image.open(BytesIO(r.content))
#         w, h = img.size
#         area = w * h

#         max_cov = 0.0
#         results = model(img, verbose=False, conf=0.3)

#         for result in results:
#             for box in result.boxes:
#                 cls = int(box.cls[0])
#                 if cls not in FOOD_CLASSES:
#                     continue

#                 x1, y1, x2, y2 = box.xyxy[0].tolist()
#                 coverage = ((x2 - x1) * (y2 - y1)) / area
#                 if coverage > max_cov:
#                     max_cov = coverage

#         return {
#             "is_zoomed": max_cov > ZOOM_THRESHOLD,
#             "coverage": max_cov
#         }

#     except Exception as e:
#         debug_print(f"YOLO filter error: {e}")
#         return {"is_zoomed": False, "coverage": 0.0}


# def filter_to_vibe_photos(photos, needed=5):
#     """Compact logging: 01. OK (4%) / 02. SKIP (42%)"""
#     vibe = []

#     for i, p in enumerate(photos):
#         if len(vibe) >= needed:
#             break

#         url = p.get("photo_url") or p.get("original")
#         if not url:
#             continue

#         info = is_zoomed_in_food_photo(url)
#         pct = int(info["coverage"] * 100)

#         if info["is_zoomed"]:
#             print(f"      {i+1:02d}. SKIP ({pct}%)")
#         else:
#             print(f"      {i+1:02d}. OK ({pct}%)")
#             vibe.append(p)

#     return vibe


# # ==============================================================================
# # VIBE ANALYSIS (unchanged)
# # ==============================================================================

# VIBE_PATTERNS = {
#     "dim_lighting": {
#         "display_name": "Dim/Romantic",
#         "patterns": [r"\bdim\b", r"\bcandle", r"\bmoody\b", r"\bambient\b"],
#     },
#     "loud_noisy": {
#         "display_name": "Loud/Noisy",
#         "patterns": [r"\bloud\b", r"\bnoisy\b", r"\bbustling\b"],
#     },
#     "quiet_intimate": {
#         "display_name": "Quiet/Intimate",
#         "patterns": [r"\bquiet\b", r"\bintimate\b", r"\bpeaceful\b"],
#     },
#     "lively_energetic": {
#         "display_name": "Lively/Energetic",
#         "patterns": [r"\blively\b", r"\bbuzz", r"\bvibrant\b"],
#     },
#     "chill_relaxed": {
#         "display_name": "Chill/Cozy",
#         "patterns": [r"\bchill\b", r"\brelax", r"\bcozy\b", r"\bcomfort"],
#     },
#     "upscale_fancy": {
#         "display_name": "Upscale/Fancy",
#         "patterns": [r"\bupscale\b", r"\bfancy\b", r"\belegant\b", r"\bchic\b"],
#     },
#     "casual": {
#         "display_name": "Casual/Divey",
#         "patterns": [r"\bcasual\b", r"\bdive", r"\bneighborhood"],
#     },
#     "romantic": {
#         "display_name": "Romantic/Date",
#         "patterns": [r"\bromantic\b", r"\bdate\b", r"\banniversary\b"],
#     },
#     "outdoor": {
#         "display_name": "Outdoor/Patio",
#         "patterns": [r"\boutdoor\b", r"\bpatio\b", r"\brooftop\b", r"\bterrace\b"],
#     },
# }


# def analyze_vibes(reviews):
#     compiled = {
#         cat: [re.compile(p, re.IGNORECASE) for p in cfg["patterns"]]
#         for cat, cfg in VIBE_PATTERNS.items()
#     }

#     counts = defaultdict(int)
#     for r in reviews:
#         text = r.get("review_text", "") or r.get("text", "") or ""
#         for cat, patterns in compiled.items():
#             if any(p.search(text) for p in patterns):
#                 counts[cat] += 1

#     sorted_v = sorted(
#         [(VIBE_PATTERNS[c]["display_name"], n) for c, n in counts.items()],
#         key=lambda x: x[1],
#         reverse=True
#     )

#     return {
#         "top_vibes": sorted_v[:5],
#         "all_counts": dict(counts),
#     }


# # ==============================================================================
# # OUTSCRAPER FUNCTIONS (FIXED)
# # ==============================================================================

# from outscraper import ApiClient


# def get_random_dc_restaurants(client, n=10):
#     """
#     Fetch up to 100 DC restaurants from Outscraper,
#     return n random names.
#     """
#     print("  🌐 Fetching DC restaurants...")

#     try:
#         results = client.google_maps_search(
#             "restaurants in washington dc",
#             limit=100,
#             language="en",
#             region="us"
#         )

#         debug_print(f"Search returned type: {type(results)}")

#         if not results:
#             print("  ❌ Empty results from search")
#             return []

#         # Handle different response structures
#         if isinstance(results, list) and len(results) > 0:
#             if isinstance(results[0], list):
#                 places = results[0]
#             else:
#                 places = results
#         else:
#             places = results

#         debug_print(f"Found {len(places)} places")

#         names = list({p["name"] for p in places if p.get("name")})

#         if len(names) < n:
#             print(f"  ❌ Only found {len(names)} restaurants.")
#             return []

#         sampled = random.sample(names, n)
#         print(f"  ✅ Selected {n} restaurants:")
#         for i, name in enumerate(sampled, 1):
#             print(f"      {i:02d}. {name}")
#         return sampled

#     except Exception as e:
#         print(f"  ❌ Restaurant fetch error: {e}")
#         import traceback
#         traceback.print_exc()
#         return []


# def get_place_id(place):
#     """
#     Extract place_id from a place dict, checking multiple possible keys.
#     Outscraper may use: place_id, google_id, or cid
#     """
#     for key in ["place_id", "google_id", "cid"]:
#         if place.get(key):
#             return place.get(key)
#     return None


# def get_restaurant_info(client, name):
#     """Single restaurant search → place_id, metadata."""
#     try:
#         res = client.google_maps_search(
#             f"{name} restaurant washington dc",
#             limit=1,
#             language="en",
#             region="us"
#         )

#         debug_print(f"Search response type: {type(res)}")

#         if not res:
#             debug_print("Empty response")
#             return None

#         # Handle nested list structure
#         if isinstance(res, list) and len(res) > 0:
#             if isinstance(res[0], list):
#                 if len(res[0]) > 0:
#                     place = res[0][0]
#                 else:
#                     debug_print("Inner list is empty")
#                     return None
#             else:
#                 place = res[0]
#         else:
#             debug_print(f"Unexpected response structure: {res}")
#             return None

#         debug_print(f"Place keys: {place.keys()}")

#         place_id = get_place_id(place)
#         debug_print(f"Extracted place_id: {place_id}")

#         if not place_id:
#             debug_print("No place_id found in any expected key")
#             return None

#         return {
#             "name": place.get("name"),
#             "place_id": place_id,
#             "rating": place.get("rating"),
#             "reviews_count": place.get("reviews") or place.get("reviews_count"),
#             "address": place.get("full_address") or place.get("address"),
#             "type": place.get("type") or place.get("category"),
#         }

#     except Exception as e:
#         print(f"  ❌ Error in get_restaurant_info: {e}")
#         import traceback
#         traceback.print_exc()
#         return None


# def get_reviews(client, place_id, limit, max_retries=2):
#     """
#     Fetch reviews for a place_id.
#     Checks multiple possible keys for the reviews data.
#     Includes retry logic for transient 500 errors.
#     """
#     import time

#     for attempt in range(max_retries + 1):
#         try:
#             debug_print(f"Fetching reviews for place_id: {place_id} (attempt {attempt + 1})")

#             res = client.google_maps_reviews(
#                 [place_id],
#                 reviews_limit=limit,
#                 language="en",
#                 sort="most_relevant"
#             )

#             debug_print(f"Reviews response type: {type(res)}")

#             if not res:
#                 debug_print("Empty reviews response")
#                 return []

#             # Debug: print full structure for first call
#             if DEBUG:
#                 try:
#                     debug_print(f"Full response structure: {json.dumps(res, indent=2, default=str)[:2000]}")
#                 except:
#                     debug_print(f"Response (raw): {str(res)[:2000]}")

#             # Handle response structure
#             if isinstance(res, list) and len(res) > 0:
#                 place_data = res[0]
#             else:
#                 place_data = res

#             debug_print(f"Place data keys: {place_data.keys() if isinstance(place_data, dict) else 'not a dict'}")

#             # Try multiple possible keys for reviews
#             reviews = None
#             for key in ["reviews_data", "reviews", "review_data", "data"]:
#                 if isinstance(place_data, dict) and key in place_data:
#                     reviews = place_data[key]
#                     debug_print(f"Found reviews under key: '{key}', count: {len(reviews) if reviews else 0}")
#                     break

#             if reviews is None:
#                 debug_print("No reviews found under any expected key")
#                 # Maybe the response itself is the reviews list?
#                 if isinstance(place_data, list):
#                     reviews = place_data
#                     debug_print(f"Using place_data directly as reviews list, count: {len(reviews)}")
#                 else:
#                     return []

#             if not reviews:
#                 debug_print("Reviews list is empty")
#                 return []

#             # Debug first review structure
#             if reviews and len(reviews) > 0:
#                 debug_print(f"First review keys: {reviews[0].keys() if isinstance(reviews[0], dict) else 'not a dict'}")

#             return sorted(reviews, key=lambda r: r.get("review_likes", 0) or 0, reverse=True)

#         except Exception as e:
#             error_msg = str(e)
#             debug_print(f"Attempt {attempt + 1} failed: {error_msg}")

#             # Retry on 500 errors
#             if "500" in error_msg and attempt < max_retries:
#                 wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s
#                 debug_print(f"Retrying in {wait_time}s...")
#                 time.sleep(wait_time)
#                 continue

#             print(f"  ❌ Error in get_reviews: {e}")
#             import traceback
#             traceback.print_exc()
#             return []

#     return []  # All retries exhausted
#     return []  # All retries exhausted


# def get_photos(client, place_id, limit):
#     """Fetch photos for a place_id."""
#     try:
#         debug_print(f"Fetching photos for place_id: {place_id}")

#         res = client.google_maps_photos(
#             [place_id],
#             photosLimit=limit,
#             language="en"
#         )

#         debug_print(f"Photos response type: {type(res)}")

#         if not res:
#             debug_print("Empty photos response")
#             return []

#         # Debug: dump raw structure
#         if DEBUG:
#             try:
#                 debug_print(f"Photos raw response: {json.dumps(res, indent=2, default=str)[:3000]}")
#             except:
#                 debug_print(f"Photos raw (str): {str(res)[:3000]}")

#         # Unwrap nested lists: [[{...}]] -> [{...}] -> {...}
#         place_data = res

#         # Keep unwrapping lists until we find a dict or list of photo dicts
#         while isinstance(place_data, list) and len(place_data) > 0:
#             first_item = place_data[0]

#             # If first item is a dict with photo-related keys, we found our place data
#             if isinstance(first_item, dict):
#                 # Check if this dict looks like place data (has 'photos' key)
#                 if any(key in first_item for key in ["photos", "photos_data", "photo_url", "original"]):
#                     # If it has 'photos' key, it's place data - extract it
#                     if "photos" in first_item or "photos_data" in first_item:
#                         place_data = first_item
#                         break
#                     # If it has 'photo_url' or 'original', this IS the photos list
#                     else:
#                         debug_print(f"Found photos list with {len(place_data)} items")
#                         return place_data
#                 # Otherwise, unwrap one more level
#                 else:
#                     place_data = first_item
#                     break
#             else:
#                 # First item is another list, keep unwrapping
#                 place_data = first_item

#         debug_print(f"Photos place_data type: {type(place_data)}")
#         debug_print(f"Photos place_data keys: {place_data.keys() if isinstance(place_data, dict) else 'not a dict'}")

#         # Now extract photos from place_data dict
#         photos = None
#         if isinstance(place_data, dict):
#             for key in ["photos", "photos_data", "images", "data"]:
#                 if key in place_data:
#                     photos = place_data[key]
#                     debug_print(f"Found photos under key: '{key}', count: {len(photos) if photos else 0}")
#                     break

#         if photos is None:
#             if isinstance(place_data, list):
#                 # Last resort: maybe it's already a photos list
#                 photos = place_data
#                 debug_print(f"Using place_data directly as photos list, count: {len(photos)}")
#             else:
#                 debug_print("Could not find photos in response")
#                 return []

#         return photos or []

#     except Exception as e:
#         print(f"  ❌ Error in get_photos: {e}")
#         import traceback
#         traceback.print_exc()
#         return []


# def download_photo(url, path):
#     try:
#         r = requests.get(url, timeout=10)
#         if r.status_code == 200:
#             path.parent.mkdir(parents=True, exist_ok=True)
#             with open(path, "wb") as f:
#                 f.write(r.content)
#             return True
#     except Exception as e:
#         debug_print(f"Download error: {e}")
#     return False


# # ==============================================================================
# # PIPELINE
# # ==============================================================================

# def process_restaurant(client, query, index):
#     print("\n" + "─" * 60)
#     print(f"[{index+1}] 🍽️  {query}")
#     print("─" * 60)

#     print("  🔍 Searching...")
#     info = get_restaurant_info(client, query)
#     if not info:
#         print("  ❌ SKIP: Not found")
#         return None

#     print(f"  ✅ Found: {info['name']} ({info['rating']}⭐)")

#     # Reviews
#     print(f"  📝 Fetching {REVIEWS_NEEDED} reviews...")
#     reviews = get_reviews(client, info["place_id"], REVIEWS_NEEDED)

#     if len(reviews) < REVIEWS_NEEDED:
#         print(f"  ❌ SKIP: Only {len(reviews)} reviews")
#         return None

#     reviews = reviews[:REVIEWS_NEEDED]
#     print(f"  ✅ Got {len(reviews)} reviews")

#     # Photos
#     print(f"  📷 Fetching {PHOTOS_TO_FETCH} photos...")
#     photos = get_photos(client, info["place_id"], PHOTOS_TO_FETCH)

#     if len(photos) < IMAGES_NEEDED:
#         print(f"  ❌ SKIP: Only {len(photos)} photos")
#         return None

#     print("  🔍 Running YOLO filter...")
#     vibe_photos = filter_to_vibe_photos(photos, IMAGES_NEEDED)

#     if len(vibe_photos) < IMAGES_NEEDED:
#         print(f"  ❌ SKIP: Only {len(vibe_photos)} vibe photos")
#         return None

#     print(f"  ✅ Kept {len(vibe_photos)} vibe photos")

#     # Vibe Analysis
#     vibe_info = analyze_vibes(reviews)
#     top = vibe_info["top_vibes"][0] if vibe_info["top_vibes"] else ("N/A", 0)
#     print(f"  🎭 Top Vibe: {top[0]} ({top[1]} mentions)")

#     # Save Photos
#     print("  💾 Saving vibe photos...")
#     safe = "".join(c if c.isalnum() else "_" for c in info["name"])[:25]
#     saved_filenames = []

#     for i, p in enumerate(vibe_photos):
#         url = p.get("photo_url") or p.get("original") or p.get("url")
#         if not url:
#             continue
#         fname = f"{safe}_vibe_{i+1}.jpg"
#         path = IMAGES_DIR / fname
#         if download_photo(url, path):
#             saved_filenames.append(fname)
#             print(f"      + {fname}")

#     return {
#         "restaurant": info,
#         "vibe_analysis": vibe_info,
#         "reviews": [
#             {
#                 "text": (r.get("review_text") or r.get("text") or "")[:300],
#                 "rating": r.get("review_rating") or r.get("rating"),
#                 "likes": r.get("review_likes", 0) or 0,
#             }
#             for r in reviews
#         ],
#         "photos": {
#             "filenames": saved_filenames,
#             "urls": [
#                 p.get("photo_url") or p.get("original") or p.get("url")
#                 for p in vibe_photos
#             ],
#         },
#     }


# def main():
#     print("=" * 60)
#     print("🍽️  VIBECHECK DC — Random Restaurant Edition (FIXED)")
#     print("=" * 60)

#     if DEBUG:
#         print("⚠️  DEBUG MODE ENABLED - verbose output")

#     if OUTSCRAPER_API_KEY == "your_outscraper_key_here":
#         print("⚠️  Please set your Outscraper API key")
#         return

#     client = ApiClient(api_key=OUTSCRAPER_API_KEY)

#     # Dynamic discovery
#     restaurant_list = get_random_dc_restaurants(client, n=10)
#     if not restaurant_list:
#         print("❌ Cannot continue — no restaurants.")
#         return

#     results = []
#     skipped = []

#     for i, name in enumerate(restaurant_list):
#         r = process_restaurant(client, name, i)
#         if r:
#             results.append(r)
#         else:
#             skipped.append(name)

#     OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
#     outpath = OUTPUT_DIR / "vibecheck_dc_results.json"

#     with open(outpath, "w") as f:
#         json.dump(results, f, indent=2)

#     print("\n" + "=" * 60)
#     print("📊 SUMMARY")
#     print("=" * 60)
#     print(f"  Kept:    {len(results)}")
#     print(f"  Skipped: {len(skipped)}")
#     print(f"  Output JSON: {outpath}")
#     print(f"  Saved images → {IMAGES_DIR}/")

#     print("\n" + "-" * 60)
#     for r in results:
#         name = r["restaurant"]["name"]
#         rating = r["restaurant"]["rating"]
#         top = r["vibe_analysis"]["top_vibes"][0][0] if r["vibe_analysis"]["top_vibes"] else "N/A"
#         print(f"{name:<35} {rating:<5} {top:<20}")

#     if skipped:
#         print("\n  Skipped restaurants:")
#         for name in skipped:
#             print(f"    - {name}")


# if __name__ == "__main__":
#     main()
