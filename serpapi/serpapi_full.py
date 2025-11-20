import hashlib
import json
import os
import time

import pandas as pd
import requests

from serpapi import GoogleSearch

##############################################################
# CONFIG
##############################################################

# REPLACE WITH YOUR KEY
SERPAPI_KEY = "api_key"  # Replace with your SerpAPI key

CSV_PATH = "../data/restaurants_info/restaurants_manual.csv"  # change this to the actual file listing all of our restaurants
IMAGE_DIR = "../data/images/restaurant_images"
PROGRESS_FILE = "image_collection_progress.json"
TEST_MODE = False

# Search terms to use for each restaurant
SEARCH_TERMS = ["interior", "exterior", "day environment", "night environment"]

# Number of images to collect per search term
IMAGES_PER_TERM = 5

# Delay between requests (seconds) to avoid rate limits
REQUEST_DELAY = 1

# SETUP
os.makedirs(IMAGE_DIR, exist_ok=True)


##############################################################
# DUPLICATE DETECTION
##############################################################
def get_image_hash(image_path):
    """Calculate MD5 hash of an image file for duplicate detection."""
    hash_md5 = hashlib.md5()
    with open(image_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_url_hash(url):
    """Calculate hash of URL for quick duplicate checking before download."""
    return hashlib.md5(url.encode()).hexdigest()


##############################################################
# PROGRESS TRACKING
##############################################################
def load_progress():
    """Load progress from JSON file."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {
        "last_completed_index": -1,
        "completed_restaurants": [],
        "downloaded_url_hashes": {},  # Track URLs to avoid re-downloading
    }


def save_progress(index, restaurant_name, url_hashes=None):
    """Save progress to JSON file."""
    progress = load_progress()
    progress["last_completed_index"] = index
    if restaurant_name not in progress["completed_restaurants"]:
        progress["completed_restaurants"].append(restaurant_name)
    if url_hashes:
        if restaurant_name not in progress["downloaded_url_hashes"]:
            progress["downloaded_url_hashes"][restaurant_name] = []
        progress["downloaded_url_hashes"][restaurant_name].extend(url_hashes)
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


##############################################################
# IMAGE DOWNLOAD
##############################################################
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


##############################################################
# SERP API IMAGE SEARCH
##############################################################
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


##############################################################
# MAIN FUNCTION
##############################################################
def collect_images_for_restaurant(restaurant_name, search_terms, images_per_term):
    """Collect images for a single restaurant across all search terms with duplicate detection."""
    # Sanitize restaurant name for file system
    safe_name = "".join(
        c if c.isalnum() or c in (" ", "-", "_") else "_" for c in restaurant_name
    )
    safe_name = safe_name.replace(" ", "_")

    # Track all URLs and image hashes for THIS restaurant to detect duplicates
    seen_url_hashes = set()
    seen_image_hashes = set()
    downloaded_url_hashes = []

    # Load existing images for this restaurant to check for duplicates
    existing_files = [f for f in os.listdir(IMAGE_DIR) if f.startswith(safe_name + "_")]
    for existing_file in existing_files:
        file_path = os.path.join(IMAGE_DIR, existing_file)
        try:
            img_hash = get_image_hash(file_path)
            seen_image_hashes.add(img_hash)
        except Exception:
            pass

    total_downloaded = 0
    total_duplicates = 0

    # Counter for unique images across all search terms
    unique_image_counter = 1

    for term in search_terms:
        query = f"{restaurant_name} restaurant Washington DC area {term}"
        print(f"  🔍 Searching: {query}")

        image_urls = search_images(query, num_images=images_per_term)

        if not image_urls:
            continue

        for url in image_urls:
            # Check if we've already seen this URL
            url_hash = get_url_hash(url)
            if url_hash in seen_url_hashes:
                print(
                    "    🔄 Skipping duplicate URL (already downloaded in different search)"
                )
                total_duplicates += 1
                continue

            seen_url_hashes.add(url_hash)

            # Determine file extension from URL or default to jpg
            ext = os.path.splitext(url.split("?")[0])[-1]
            if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
                ext = ".jpg"

            # Use unique counter instead of per-term counter
            filename = f"{safe_name}_{term}_{unique_image_counter}{ext}"
            save_path = os.path.join(IMAGE_DIR, filename)

            # Skip if already exists
            if os.path.exists(save_path):
                print(f"    ⏭️  Skipping (already exists): {filename}")
                continue

            # Download the image
            if download_image(url, save_path):
                # Check if image content is duplicate by comparing hashes
                try:
                    img_hash = get_image_hash(save_path)
                    if img_hash in seen_image_hashes:
                        print(
                            "    🔄 Duplicate image detected (same content, different URL) - removing"
                        )
                        os.remove(save_path)
                        total_duplicates += 1
                        continue

                    seen_image_hashes.add(img_hash)
                    downloaded_url_hashes.append(url_hash)
                    total_downloaded += 1
                    unique_image_counter += 1
                    print(f"    ✅ Downloaded: {filename}")
                except Exception as e:
                    print(f"    ⚠️  Error checking image hash: {e}")
                    total_downloaded += 1
                    unique_image_counter += 1

            time.sleep(0.2)  # Small delay between image downloads

        time.sleep(REQUEST_DELAY)  # Delay between search queries

    print(
        f"  📊 Summary: {total_downloaded} unique images, {total_duplicates} duplicates removed"
    )
    return total_downloaded, downloaded_url_hashes


##############################################################
# MAIN SCRIPT
##############################################################
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
            downloaded, url_hashes = collect_images_for_restaurant(
                restaurant, SEARCH_TERMS, IMAGES_PER_TERM
            )
            print(f"  ✅ Completed: {downloaded} unique images downloaded")

            # Save progress after each restaurant
            save_progress(idx, restaurant, url_hashes)

        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user. Progress saved.")
            print(f"Resume from restaurant index: {idx}")
            break
        except Exception as e:
            print(f"  ❌ Error processing {restaurant}: {e}")
            import traceback

            traceback.print_exc()
            # Save progress even on error
            save_progress(idx, restaurant)
            continue

    print(f"\n{'='*60}")
    print("🎉 Image collection complete!")
    print(f"Images saved to: {IMAGE_DIR}/")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
