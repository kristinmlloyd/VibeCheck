import os
import sqlite3

import clip
import faiss
import numpy as np
import torch
from PIL import Image
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

DB_PATH = "restaurants.db"
IMAGE_DIR = "sample_images"
FAISS_PATH = "vibecheck_index.faiss"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print("Loading models...")
text_model = SentenceTransformer("all-MiniLM-L6-v2", device=DEVICE)
clip_model, clip_preprocess = clip.load("ViT-B/32", device=DEVICE)

conn = sqlite3.connect(DB_PATH)
rows = conn.execute("SELECT id, name, review_snippet FROM restaurants").fetchall()
print(f"Loaded {len(rows)} rows")

embeddings, meta_ids = [], []

for biz_id, name, review in tqdm(rows, desc="Embedding"):
    text_vec = text_model.encode(
        review or name or "", convert_to_numpy=True, normalize_embeddings=True
    )

    img_path = os.path.join(IMAGE_DIR, f"{biz_id}.jpg")
    if os.path.exists(img_path):
        try:
            image = clip_preprocess(Image.open(img_path)).unsqueeze(0).to(DEVICE)
            with torch.no_grad():
                img_vec = clip_model.encode_image(image)
            img_vec /= img_vec.norm(dim=-1, keepdim=True)
            img_vec = img_vec.cpu().numpy()[0]
        except:
            img_vec = np.zeros((512,))
    else:
        img_vec = np.zeros((512,))

    combined = np.concatenate([text_vec, img_vec]).astype("float32")
    embeddings.append(combined)
    meta_ids.append(biz_id)

embeddings = np.vstack(embeddings).astype("float32")

dim = embeddings.shape[1]
index = faiss.IndexFlatIP(dim)
index.add(embeddings)
faiss.write_index(index, FAISS_PATH)
np.save("meta_ids.npy", np.array(meta_ids))
np.save("vibe_embeddings.npy", embeddings)

print(f"FAISS index saved to {FAISS_PATH} with {len(meta_ids)} entries")
