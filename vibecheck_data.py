# # import os
# # import time
# # import requests
# # import pandas as pd
# # import sqlite3
# # from tqdm import tqdm
# # from PIL import Image
# # from io import BytesIO

# # #load_dotenv()

# # API_KEY =  "nFrk1eYpZ5PkuCuzicLfqUSvRGNEojVz6Jpz-aB3sdzqfJJcDz_yURztZ_kjDqescGSojb-PYef13gJHkSbq4qgXNP6KfvF90DLMYIxPB_ajKZiycdkZrzRq_T8RaXYx" #os.getenv("YELP_API_KEY")  # pulls it from your .env file
# # HEADERS = {"Authorization": f"Bearer {API_KEY}"}
# # SEARCH_URL = "https://api.yelp.com/v3/businesses/search"
# # REVIEW_URL = "https://api.yelp.com/v3/businesses/{id}/reviews"

# # CITY = "New York, NY"
# # CATEGORIES = "restaurants"
# # LIMIT = 50
# # MAX_PAGES = 4 

# # DB_PATH = "restaurants.db"
# # IMAGE_DIR = "sample_images"
# # os.makedirs(IMAGE_DIR, exist_ok=True)

# # def yelp_search(offset=0):
# #     params = {
# #         "location": CITY,
# #         "categories": CATEGORIES,
# #         "limit": LIMIT,
# #         "offset": offset,
# #         "sort_by": "rating"
# #     }
# #     r = requests.get(SEARCH_URL, headers=HEADERS, params=params)
# #     if r.status_code != 200:
# #         print("❌ Error:", r.status_code, r.text)
# #     r.raise_for_status()
# #     return r.json().get("businesses", [])


# # def get_reviews(biz_id):
# #     try:
# #         r = requests.get(REVIEW_URL.format(id=biz_id), headers=HEADERS)
# #         r.raise_for_status()
# #         reviews = r.json().get("reviews", [])
# #         texts = [rev["text"] for rev in reviews]
# #         return " ".join(texts)
# #     except Exception:
# #         return ""

# # print(f"Collecting Yelp data for {CITY}...")
# # all_businesses = []
# # for i in tqdm(range(MAX_PAGES)):
# #     batch = yelp_search(offset=i * LIMIT)
# #     if not batch:
# #         break
# #     all_businesses.extend(batch)
# #     time.sleep(0.5)

# # print(f"Collected {len(all_businesses)} businesses")


# # rows = []
# # for biz in tqdm(all_businesses, desc="Processing"):
# #     rec = {
# #         "id": biz["id"],
# #         "name": biz["name"],
# #         "rating": biz.get("rating"),
# #         "review_count": biz.get("review_count"),
# #         "price": biz.get("price", ""),
# #         "city": biz["location"]["city"],
# #         "address": " ".join(biz["location"].get("display_address", [])),
# #         "categories": ", ".join([c["title"] for c in biz["categories"]]),
# #         "image_url": biz.get("image_url"),
# #         "review_snippet": get_reviews(biz["id"])
# #     }
# #     rows.append(rec)
# #     time.sleep(0.3)

# # df = pd.DataFrame(rows)

# # def download_image(biz_id, url):
# #     if not url:
# #         return
# #     try:
# #         img = Image.open(BytesIO(requests.get(url).content)).convert("RGB")
# #         img.save(os.path.join(IMAGE_DIR, f"{biz_id}.jpg"))
# #     except Exception:
# #         pass

# # print("Downloading images...")
# # for _, r in tqdm(df.iterrows(), total=len(df)):
# #     download_image(r["id"], r["image_url"])

# # conn = sqlite3.connect(DB_PATH)
# # df.to_sql("restaurants", conn, if_exists="replace", index=False)
# # conn.close()

# # print(f"Saved {len(df)} restaurants to {DB_PATH}")
# # print(f"Images in {IMAGE_DIR}/")


# import os
# import time
# import math
# import requests
# import pandas as pd
# import sqlite3
# from tqdm import tqdm
# from PIL import Image
# from io import BytesIO
# from concurrent.futures import ThreadPoolExecutor, as_completed

# # ==========================
# # CONFIG
# # ==========================
# API_KEY = "nFrk1eYpZ5PkuCuzicLfqUSvRGNEojVz6Jpz-aB3sdzqfJJcDz_yURztZ_kjDqescGSojb-PYef13gJHkSbq4qgXNP6KfvF90DLMYIxPB_ajKZiycdkZrzRq_T8RaXYx"  # ⚠️ Replace with your Yelp API Key
# HEADERS = {"Authorization": f"Bearer {API_KEY}"}

# SEARCH_URL = "https://api.yelp.com/v3/businesses/search"
# REVIEW_URL = "https://api.yelp.com/v3/businesses/{id}/reviews"

# CATEGORIES = "restaurants"
# LIMIT = 50          # Yelp max per request
# MAX_OFFSET = 950    # Yelp max offset

# DB_PATH = "restaurants.db"
# IMAGE_DIR = "sample_images"
# os.makedirs(IMAGE_DIR, exist_ok=True)

# # ==========================
# # DC BOUNDING BOX (lat/lon)
# # ==========================
# LAT_MIN, LAT_MAX = 38.79, 38.99
# LON_MIN, LON_MAX = -77.12, -76.90
# GRID_SIZE = 0.02  # ~2 km per square

# MAX_THREADS = 4  # adjust depending on your CPU/connection

# # ==========================
# # HELPER FUNCTIONS
# # ==========================
# def yelp_search(lat, lon, offset=0):
#     """Search businesses in a grid square."""
#     params = {
#         "latitude": lat,
#         "longitude": lon,
#         "categories": CATEGORIES,
#         "limit": LIMIT,
#         "offset": offset,
#         "sort_by": "rating"
#     }
#     try:
#         r = requests.get(SEARCH_URL, headers=HEADERS, params=params)
#         r.raise_for_status()
#         return r.json().get("businesses", [])
#     except Exception as e:
#         print(f"Search error at ({lat},{lon}) offset {offset}: {e}")
#         return []

# def get_reviews(biz_id):
#     """Get up to 3 Yelp reviews per business."""
#     try:
#         r = requests.get(REVIEW_URL.format(id=biz_id), headers=HEADERS)
#         r.raise_for_status()
#         reviews = r.json().get("reviews", [])
#         return " ".join([rev["text"] for rev in reviews])
#     except:
#         return ""

# def download_image(biz_id, url):
#     """Download main image per business."""
#     if not url:
#         return
#     try:
#         img = Image.open(BytesIO(requests.get(url).content)).convert("RGB")
#         img.save(os.path.join(IMAGE_DIR, f"{biz_id}.jpg"))
#     except:
#         pass

# def generate_grid(lat_min, lat_max, lon_min, lon_max, step):
#     """Generate center points for the DC grid."""
#     lat_steps = int(math.ceil((lat_max - lat_min)/step))
#     lon_steps = int(math.ceil((lon_max - lon_min)/step))
#     grid = []
#     for i in range(lat_steps):
#         for j in range(lon_steps):
#             lat = lat_min + i*step + step/2
#             lon = lon_min + j*step + step/2
#             grid.append((lat, lon))
#     return grid

# # ==========================
# # GRID POINTS
# # ==========================
# grid_points = generate_grid(LAT_MIN, LAT_MAX, LON_MIN, LON_MAX, GRID_SIZE)
# print(f"Total grid points: {len(grid_points)}")

# # ==========================
# # FETCH BUSINESSES
# # ==========================
# all_businesses = {}

# def fetch_grid_point(lat_lon):
#     lat, lon = lat_lon
#     businesses = {}
#     offset = 0
#     while True:
#         batch = yelp_search(lat, lon, offset)
#         if not batch:
#             break
#         for biz in batch:
#             businesses[biz["id"]] = biz
#         offset += LIMIT
#         if offset > MAX_OFFSET:
#             break
#         time.sleep(0.1)  # be polite
#     return businesses

# print("\nFetching businesses with concurrency...")
# with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
#     futures = {executor.submit(fetch_grid_point, gp): gp for gp in grid_points}
#     for future in tqdm(as_completed(futures), total=len(futures)):
#         result = future.result()
#         all_businesses.update(result)

# print(f"\nTotal unique businesses collected: {len(all_businesses)}")

# # ==========================
# # PROCESS BUSINESSES
# # ==========================
# rows = []

# def process_business(biz):
#     """Fetch reviews and prepare record."""
#     rec = {
#         "id": biz["id"],
#         "name": biz["name"],
#         "rating": biz.get("rating"),
#         "review_count": biz.get("review_count"),
#         "price": biz.get("price", ""),
#         "city": biz["location"]["city"],
#         "address": " ".join(biz["location"].get("display_address", [])),
#         "categories": ", ".join([c["title"] for c in biz["categories"]]),
#         "image_url": biz.get("image_url"),
#         "review_snippet": get_reviews(biz["id"])
#     }
#     download_image(biz["id"], biz.get("image_url"))
#     return rec

# print("\nProcessing businesses and downloading images with concurrency...")
# with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
#     futures = {executor.submit(process_business, biz): biz_id for biz_id, biz in all_businesses.items()}
#     for future in tqdm(as_completed(futures), total=len(futures)):
#         row = future.result()
#         rows.append(row)

# df = pd.DataFrame(rows)

# # ==========================
# # SAVE TO SQLITE
# # ==========================
# conn = sqlite3.connect(DB_PATH)
# df.to_sql("restaurants", conn, if_exists="replace", index=False)
# conn.close()

# print(f"\nSaved {len(df)} businesses to {DB_PATH}")
# print(f"Images stored in {IMAGE_DIR}/")

# import os
# import time
# import math
# import requests
# import pandas as pd
# import sqlite3
# from tqdm import tqdm
# from PIL import Image
# from io import BytesIO
# from concurrent.futures import ThreadPoolExecutor, as_completed

# # ==========================
# # CONFIG
# # ==========================
# API_KEY = "nFrk1eYpZ5PkuCuzicLfqUSvRGNEojVz6Jpz-aB3sdzqfJJcDz_yURztZ_kjDqescGSojb-PYef13gJHkSbq4qgXNP6KfvF90DLMYIxPB_ajKZiycdkZrzRq_T8RaXYx"   # ⚠️ Replace with your Yelp API key
# HEADERS = {"Authorization": f"Bearer {API_KEY}"}

# SEARCH_URL = "https://api.yelp.com/v3/businesses/search"
# REVIEW_URL = "https://api.yelp.com/v3/businesses/{id}/reviews"

# CATEGORIES = [
#     "restaurants", "cafes", "bakeries", "bars", "diners"
# ]

# LIMIT = 50
# MAX_OFFSET = 950
# DB_PATH = "restaurants.db"
# IMAGE_DIR = "sample_images"
# os.makedirs(IMAGE_DIR, exist_ok=True)

# LAT_MIN, LAT_MAX = 38.79, 38.99
# LON_MIN, LON_MAX = -77.12, -76.90
# GRID_SIZE = 0.02  # ~2 km per square

# MAX_THREADS = 2  # reduce to avoid 429 errors
# RETRY_DELAY = 5  # seconds to wait after 429

# # ==========================
# # HELPER FUNCTIONS
# # ==========================
# def yelp_search(lat, lon, category, offset=0):
#     params = {
#         "latitude": lat,
#         "longitude": lon,
#         "categories": category,
#         "limit": LIMIT,
#         "offset": offset,
#         "sort_by": "rating"
#     }
#     try:
#         r = requests.get(SEARCH_URL, headers=HEADERS, params=params)
#         if r.status_code == 429:
#             time.sleep(RETRY_DELAY)
#             r = requests.get(SEARCH_URL, headers=HEADERS, params=params)
#         r.raise_for_status()
#         return r.json().get("businesses", [])
#     except Exception as e:
#         print(f"Search error at ({lat},{lon}) offset {offset}, category {category}: {e}")
#         return []

# def get_reviews(biz_id):
#     try:
#         r = requests.get(REVIEW_URL.format(id=biz_id), headers=HEADERS)
#         if r.status_code == 429:
#             time.sleep(RETRY_DELAY)
#             r = requests.get(REVIEW_URL.format(id=biz_id), headers=HEADERS)
#         r.raise_for_status()
#         reviews = r.json().get("reviews", [])
#         return " ".join([rev["text"] for rev in reviews])
#     except:
#         return ""

# def download_image(biz_id, url):
#     if not url:
#         return
#     try:
#         img = Image.open(BytesIO(requests.get(url).content)).convert("RGB")
#         img.save(os.path.join(IMAGE_DIR, f"{biz_id}.jpg"))
#     except:
#         pass

# def generate_grid(lat_min, lat_max, lon_min, lon_max, step):
#     lat_steps = int(math.ceil((lat_max - lat_min)/step))
#     lon_steps = int(math.ceil((lon_max - lon_min)/step))
#     grid = []
#     for i in range(lat_steps):
#         for j in range(lon_steps):
#             lat = lat_min + i*step + step/2
#             lon = lon_min + j*step + step/2
#             grid.append((lat, lon))
#     return grid

# # ==========================
# # GRID POINTS
# # ==========================
# grid_points = generate_grid(LAT_MIN, LAT_MAX, LON_MIN, LON_MAX, GRID_SIZE)
# print(f"Total grid points: {len(grid_points)}")

# # ==========================
# # FETCH BUSINESSES
# # ==========================
# all_businesses = {}

# def fetch_grid_category(lat_lon_category):
#     lat, lon, category = lat_lon_category
#     businesses = {}
#     offset = 0
#     while True:
#         batch = yelp_search(lat, lon, category, offset)
#         if not batch:
#             break
#         for biz in batch:
#             businesses[biz["id"]] = biz
#         offset += LIMIT
#         if offset > MAX_OFFSET:
#             break
#         time.sleep(0.1)
#     return businesses

# print("\nFetching businesses with concurrency...")
# tasks = [(lat, lon, cat) for lat, lon in grid_points for cat in CATEGORIES]

# with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
#     futures = {executor.submit(fetch_grid_category, t): t for t in tasks}
#     for future in tqdm(as_completed(futures), total=len(futures)):
#         result = future.result()
#         all_businesses.update(result)

# print(f"\nTotal unique businesses collected: {len(all_businesses)}")

# # ==========================
# # PROCESS BUSINESSES
# # ==========================
# rows = []

# def process_business(biz):
#     rec = {
#         "id": biz["id"],
#         "name": biz["name"],
#         "rating": biz.get("rating"),
#         "review_count": biz.get("review_count"),
#         "price": biz.get("price", ""),
#         "city": biz["location"]["city"],
#         "address": " ".join(biz["location"].get("display_address", [])),
#         "categories": ", ".join([c["title"] for c in biz["categories"]]),
#         "image_url": biz.get("image_url"),
#         "review_snippet": get_reviews(biz["id"])
#     }
#     download_image(biz["id"], biz.get("image_url"))
#     return rec

# print("\nProcessing businesses and downloading images with concurrency...")
# with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
#     futures = {executor.submit(process_business, biz): biz_id for biz_id, biz in all_businesses.items()}
#     for future in tqdm(as_completed(futures), total=len(futures)):
#         row = future.result()
#         rows.append(row)

# df = pd.DataFrame(rows)

# # ==========================
# # SAVE TO SQLITE
# # ==========================
# conn = sqlite3.connect(DB_PATH)
# df.to_sql("restaurants", conn, if_exists="replace", index=False)
# conn.close()

# print(f"\nSaved {len(df)} businesses to {DB_PATH}")
# print(f"Images stored in {IMAGE_DIR}/")

# import os
# import time
# import requests
# import pandas as pd
# import sqlite3
# from tqdm import tqdm
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from PIL import Image
# from io import BytesIO
# import math

# # ==========================
# # CONFIG
# # ==========================
# API_KEY = "nFrk1eYpZ5PkuCuzicLfqUSvRGNEojVz6Jpz-aB3sdzqfJJcDz_yURztZ_kjDqescGSojb-PYef13gJHkSbq4qgXNP6KfvF90DLMYIxPB_ajKZiycdkZrzRq_T8RaXYx"
# HEADERS = {"Authorization": f"Bearer {API_KEY}"}

# SEARCH_URL = "https://api.yelp.com/v3/businesses/search"
# REVIEW_URL = "https://api.yelp.com/v3/businesses/{id}/reviews"

# DB_PATH = "restaurants.db"
# IMAGE_DIR = "sample_images"
# os.makedirs(IMAGE_DIR, exist_ok=True)

# CATEGORIES = ["restaurants", "cafes", "bakeries", "bars", "diners"]
# LIMIT = 50  # Yelp max per request
# MAX_THREADS = 1  # keep low to avoid rate-limits
# MAX_OFFSET = 950  # Yelp max offset per query

# # DC bounding box (example)
# LAT_MIN, LAT_MAX = 38.79, 38.99
# LON_MIN, LON_MAX = -77.12, -76.90
# GRID_STEP = 0.02  # ~2 km per grid square

# DELAY_BETWEEN_REQUESTS = 0.5  # seconds

# # ==========================
# # GRID GENERATION
# # ==========================
# def generate_grid(lat_min, lat_max, lon_min, lon_max, step):
#     lat_steps = int(math.ceil((lat_max - lat_min)/step))
#     lon_steps = int(math.ceil((lon_max - lon_min)/step))
#     grid = []
#     for i in range(lat_steps):
#         for j in range(lon_steps):
#             lat = lat_min + i*step + step/2
#             lon = lon_min + j*step + step/2
#             grid.append((lat, lon))
#     return grid

# grid_points = generate_grid(LAT_MIN, LAT_MAX, LON_MIN, LON_MAX, GRID_STEP)
# print(f"Total grid points: {len(grid_points)}")

# # ==========================
# # Yelp Search with retry/backoff
# # ==========================
# def yelp_search(lat, lon, category, offset=0, max_retries=5):
#     params = {
#         "latitude": lat,
#         "longitude": lon,
#         "categories": category,
#         "limit": LIMIT,
#         "offset": offset,
#         "sort_by": "rating"
#     }
#     for attempt in range(max_retries):
#         try:
#             r = requests.get(SEARCH_URL, headers=HEADERS, params=params)
#             if r.status_code == 429:
#                 wait = 2 ** attempt
#                 print(f"429 rate limit at ({lat},{lon}) category {category}, waiting {wait}s...")
#                 time.sleep(wait)
#                 continue
#             r.raise_for_status()
#             return r.json().get("businesses", [])
#         except requests.exceptions.RequestException as e:
#             print(f"Error at ({lat},{lon}) category {category} offset {offset}: {e}")
#             time.sleep(2)
#     return []

# # ==========================
# # Get multiple reviews per business
# # ==========================
# def get_reviews(biz_id):
#     try:
#         r = requests.get(REVIEW_URL.format(id=biz_id), headers=HEADERS)
#         r.raise_for_status()
#         reviews = r.json().get("reviews", [])
#         texts = [rev["text"] for rev in reviews]
#         return " ".join(texts)
#     except Exception:
#         return ""

# # ==========================
# # Download images
# # ==========================
# def download_image(biz_id, url):
#     if not url:
#         return
#     try:
#         img = Image.open(BytesIO(requests.get(url).content)).convert("RGB")
#         img.save(os.path.join(IMAGE_DIR, f"{biz_id}.jpg"))
#     except Exception:
#         pass

# # ==========================
# # FETCH ALL BUSINESSES
# # ==========================
# all_businesses = {}

# for lat, lon in tqdm(grid_points):
#     for category in CATEGORIES:
#         offset = 0
#         while offset <= MAX_OFFSET:
#             batch = yelp_search(lat, lon, category, offset)
#             if not batch:
#                 break
#             for biz in batch:
#                 all_businesses[biz["id"]] = biz
#             offset += LIMIT
#             time.sleep(DELAY_BETWEEN_REQUESTS)

# print(f"Total unique businesses collected: {len(all_businesses)}")

# # ==========================
# # PROCESS BUSINESSES AND DOWNLOAD IMAGES
# # ==========================
# rows = []

# def process_business(biz):
#     rec = {
#         "id": biz["id"],
#         "name": biz["name"],
#         "rating": biz.get("rating"),
#         "review_count": biz.get("review_count"),
#         "price": biz.get("price", ""),
#         "city": biz["location"]["city"],
#         "address": " ".join(biz["location"].get("display_address", [])),
#         "categories": ", ".join([c["title"] for c in biz["categories"]]),
#         "image_url": biz.get("image_url"),
#         "review_snippet": get_reviews(biz["id"])
#     }
#     download_image(biz["id"], biz.get("image_url"))
#     return rec

# print("Processing businesses and downloading images with concurrency...")
# with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
#     futures = {executor.submit(process_business, biz): biz_id for biz_id, biz in all_businesses.items()}
#     for future in tqdm(as_completed(futures), total=len(futures)):
#         rows.append(future.result())

# df = pd.DataFrame(rows)

# # ==========================
# # SAVE TO SQLITE
# # ==========================
# conn = sqlite3.connect(DB_PATH)
# df.to_sql("restaurants", conn, if_exists="replace", index=False)
# conn.close()

# print(f"Saved {len(df)} businesses to {DB_PATH}")
# print(f"Images stored in {IMAGE_DIR}/")


import os
import time
import requests

# ==========================
# CONFIG
# ==========================
API_KEY = "nFrk1eYpZ5PkuCuzicLfqUSvRGNEojVz6Jpz-aB3sdzqfJJcDz_yURztZ_kjDqescGSojb-PYef13gJHkSbq4qgXNP6KfvF90DLMYIxPB_ajKZiycdkZrzRq_T8RaXYx"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
}

SEARCH_URL = "https://api.yelp.com/v3/businesses/search"

CATEGORY = "restaurants"
LIMIT = 5  # small test
LAT = 38.8951  # DC center
LON = -77.0364
MAX_RETRIES = 5
DELAY_BEFORE_START = 5  # wait before first request
DELAY_BETWEEN_RETRIES = 2

# ==========================
# WAIT BEFORE START
# ==========================
print(f"Waiting {DELAY_BEFORE_START}s before first request to avoid 429...")
time.sleep(DELAY_BEFORE_START)

# ==========================
# SEARCH FUNCTION WITH BACKOFF
# ==========================
def yelp_search(lat, lon, category, limit=LIMIT, offset=0, max_retries=MAX_RETRIES):
    params = {
        "latitude": lat,
        "longitude": lon,
        "categories": category,
        "limit": limit,
        "offset": offset,
        "sort_by": "rating"
    }
    for attempt in range(max_retries):
        try:
            r = requests.get(SEARCH_URL, headers=HEADERS, params=params)
            if r.status_code == 429:
                wait = 2 ** attempt
                print(f"429 rate limit, waiting {wait}s...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json().get("businesses", [])
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}, retrying in {DELAY_BETWEEN_RETRIES}s...")
            time.sleep(DELAY_BETWEEN_RETRIES)
    return []

# ==========================
# RUN TEST
# ==========================
businesses = yelp_search(LAT, LON, CATEGORY)
if not businesses:
    print("No businesses returned. API key may be blocked or rate-limited.")
else:
    print(f"Collected {len(businesses)} businesses:")
    for biz in businesses:
        print(f"- {biz['name']} ({biz.get('rating', 'N/A')}⭐)")

