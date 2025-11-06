import os
import time
import requests
import pandas as pd
import sqlite3
from tqdm import tqdm
from PIL import Image
from io import BytesIO

load_dotenv()

API_KEY = os.getenv("YELP_API_KEY")  # pulls it from your .env file
HEADERS = {"Authorization": f"Bearer {API_KEY}"}
SEARCH_URL = "https://api.yelp.com/v3/businesses/search"
REVIEW_URL = "https://api.yelp.com/v3/businesses/{id}/reviews"

CITY = "New York, NY"
CATEGORIES = "restaurants"
LIMIT = 50
MAX_PAGES = 4 

DB_PATH = "restaurants.db"
IMAGE_DIR = "sample_images"
os.makedirs(IMAGE_DIR, exist_ok=True)

def yelp_search(offset=0):
    params = {
        "location": CITY,
        "categories": CATEGORIES,
        "limit": LIMIT,
        "offset": offset,
        "sort_by": "rating"
    }
    r = requests.get(SEARCH_URL, headers=HEADERS, params=params)
    if r.status_code != 200:
        print("❌ Error:", r.status_code, r.text)
    r.raise_for_status()
    return r.json().get("businesses", [])


def get_reviews(biz_id):
    try:
        r = requests.get(REVIEW_URL.format(id=biz_id), headers=HEADERS)
        r.raise_for_status()
        reviews = r.json().get("reviews", [])
        texts = [rev["text"] for rev in reviews]
        return " ".join(texts)
    except Exception:
        return ""

print(f"Collecting Yelp data for {CITY}...")
all_businesses = []
for i in tqdm(range(MAX_PAGES)):
    batch = yelp_search(offset=i * LIMIT)
    if not batch:
        break
    all_businesses.extend(batch)
    time.sleep(0.5)

print(f"Collected {len(all_businesses)} businesses")


rows = []
for biz in tqdm(all_businesses, desc="Processing"):
    rec = {
        "id": biz["id"],
        "name": biz["name"],
        "rating": biz.get("rating"),
        "review_count": biz.get("review_count"),
        "price": biz.get("price", ""),
        "city": biz["location"]["city"],
        "address": " ".join(biz["location"].get("display_address", [])),
        "categories": ", ".join([c["title"] for c in biz["categories"]]),
        "image_url": biz.get("image_url"),
        "review_snippet": get_reviews(biz["id"])
    }
    rows.append(rec)
    time.sleep(0.3)

df = pd.DataFrame(rows)

def download_image(biz_id, url):
    if not url:
        return
    try:
        img = Image.open(BytesIO(requests.get(url).content)).convert("RGB")
        img.save(os.path.join(IMAGE_DIR, f"{biz_id}.jpg"))
    except Exception:
        pass

print("Downloading images...")
for _, r in tqdm(df.iterrows(), total=len(df)):
    download_image(r["id"], r["image_url"])

conn = sqlite3.connect(DB_PATH)
df.to_sql("restaurants", conn, if_exists="replace", index=False)
conn.close()

print(f"Saved {len(df)} restaurants to {DB_PATH}")
print(f"Images in {IMAGE_DIR}/")
