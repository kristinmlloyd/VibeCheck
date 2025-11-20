import json
import os
import time

import pandas as pd
import requests

from serpapi import GoogleSearch

# ==========================
# CONFIG
# ==========================
SERPAPI_KEY = "api_key"  # Replace with your SerpAPI key
CSV_PATH = "restaurants_manual.csv"
IMAGE_DIR = "restaurant_images"
PROGRESS_FILE = "image_collection_progress.json"

# ⭐ TEST MODE - Set to True to test with first 2 restaurants only
TEST_MODE = True
TEST_LIMIT = 2  # Number of restaurants to test with

# Search terms to use for each restaurant
SEARCH_TERMS = ["interior", "exterior", "environment", "aesthetic"]

# Number of images to collect per search term
IMAGES_PER_TERM = 5  # Adjust based on your needs

# Delay between requests (seconds) to avoid rate limits
REQUEST_DELAY = 1

# ==========================
# SETUP
# ==========================
os.makedirs(IMAGE_DIR, exist_ok=True)


# ==========================
# PROGRESS TRACKING
# ==========================
def load_progress():
    """Load progress from JSON file."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"last_completed_index": -1, "completed_restaurants": []}


def save_progress(index, restaurant_name):
    """Save progress to JSON file."""
    progress = load_progress()
    progress["last_completed_index"] = index
    if restaurant_name not in progress["completed_restaurants"]:
        progress["completed_restaurants"].append(restaurant_name)
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


# ==========================
# IMAGE DOWNLOAD
# ==========================
def download_image(url, save_path, timeout=10):
    """Download an image from URL and save to disk."""
    try:
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"  ⚠️  Failed to download {save_path}: {e}")
        return False


# ==========================
# SERPAPI IMAGE SEARCH
# ==========================
def search_images(query, num_images=10):
    """Search for images using SerpAPI and return image URLs."""
    try:
        params = {
            "engine": "google_images",
            "q": query,
            "api_key": SERPAPI_KEY,
            "num": num_images,
        }
        search = GoogleSearch(params)
        results = search.get_dict()

        if "images_results" in results:
            return [img["original"] for img in results["images_results"][:num_images]]
        else:
            print(f"  ⚠️  No images found for: {query}")
            return []
    except Exception as e:
        print(f"  ❌ SerpAPI error for '{query}': {e}")
        return []


# ==========================
# MAIN COLLECTION FUNCTION
# ==========================
def collect_images_for_restaurant(restaurant_name, search_terms, images_per_term):
    """Collect images for a single restaurant across all search terms."""
    # Sanitize restaurant name for file system
    safe_name = "".join(
        c if c.isalnum() or c in (" ", "-", "_") else "_" for c in restaurant_name
    )
    safe_name = safe_name.replace(" ", "_")

    total_downloaded = 0

    for term in search_terms:
        query = f"{restaurant_name} restaurant Washington DC area {term}"
        print(f"  🔍 Searching: {query}")

        image_urls = search_images(query, num_images=images_per_term)

        if not image_urls:
            continue

        for idx, url in enumerate(image_urls, start=1):
            # Determine file extension from URL or default to jpg
            ext = os.path.splitext(url.split("?")[0])[-1]
            if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
                ext = ".jpg"

            filename = f"{safe_name}_{term}_{idx}{ext}"
            save_path = os.path.join(IMAGE_DIR, filename)

            # Skip if already exists
            if os.path.exists(save_path):
                print(f"    ⏭️  Skipping (already exists): {filename}")
                continue

            if download_image(url, save_path):
                total_downloaded += 1
                print(f"    ✅ Downloaded: {filename}")

            time.sleep(0.2)  # Small delay between image downloads

        time.sleep(REQUEST_DELAY)  # Delay between search queries

    return total_downloaded


# ==========================
# MAIN SCRIPT
# ==========================
def main():
    # Load restaurant names
    df = pd.read_csv(CSV_PATH)

    # Assuming the CSV has a column named 'name' - adjust if different
    if "name" not in df.columns:
        # If no header, assume first column is names
        df.columns = ["name"]

    restaurants = df["name"].tolist()

    # Apply test mode limit if enabled
    if TEST_MODE:
        restaurants = restaurants[:TEST_LIMIT]
        print(
            f"\n⚠️  TEST MODE ENABLED - Processing only first {TEST_LIMIT} restaurants"
        )

    # Load progress
    progress = load_progress()
    start_index = progress["last_completed_index"] + 1

    print(f"\n{'='*60}")
    print("🍽️  RESTAURANT IMAGE COLLECTION")
    print(f"{'='*60}")
    print(f"Total restaurants: {len(restaurants)}")
    print(f"Starting from index: {start_index}")
    print(f"Remaining: {len(restaurants) - start_index}")
    print(f"{'='*60}\n")

    if start_index >= len(restaurants):
        print("✅ All restaurants already processed!")
        return

    # Process restaurants
    for idx in range(start_index, len(restaurants)):
        restaurant = restaurants[idx]
        print(f"\n[{idx + 1}/{len(restaurants)}] Processing: {restaurant}")

        try:
            downloaded = collect_images_for_restaurant(
                restaurant, SEARCH_TERMS, IMAGES_PER_TERM
            )
            print(f"  ✅ Completed: {downloaded} images downloaded")

            # Save progress after each restaurant
            save_progress(idx, restaurant)

        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user. Progress saved.")
            print(f"Resume from restaurant index: {idx}")
            break
        except Exception as e:
            print(f"  ❌ Error processing {restaurant}: {e}")
            # Save progress even on error
            save_progress(idx, restaurant)
            continue

    print(f"\n{'='*60}")
    print("🎉 Image collection complete!")
    print(f"Images saved to: {IMAGE_DIR}/")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
