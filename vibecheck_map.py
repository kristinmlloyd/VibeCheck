import os
import numpy as np
import pandas as pd
import sqlite3
import umap
import hdbscan
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns

import matplotlib
matplotlib.use("Agg")

DB_PATH = "restaurants.db"
FAISS_META_PATH = "meta_ids.npy"
EMBED_PATH = "vibecheck_index.faiss"  
EMBED_CACHE = "vibe_embeddings.npy"   
OUTPUT_CSV = "vibe_map.csv"


print("Loading embeddings...")
if not os.path.exists(EMBED_CACHE):
    raise FileNotFoundError("Run vibecheck_embeddings.py first with save_embeddings=True.")

embeddings = np.load(EMBED_CACHE)
meta_ids = np.load(FAISS_META_PATH)
conn = sqlite3.connect(DB_PATH)

names = []
ratings = []
cats = []

for rid in tqdm(meta_ids):
    row = conn.execute("SELECT name, rating, categories FROM restaurants WHERE id=?", (rid,)).fetchone()
    if row:
        n, r, c = row
        names.append(n)
        ratings.append(r)
        cats.append(c)
    else:
        names.append("Unknown")
        ratings.append(None)
        cats.append("")

print(f"Loaded {len(names)} metadata entries.")

print("Running UMAP projection (2D)...")
reducer = umap.UMAP(n_neighbors=10, min_dist=0.05, metric="cosine", random_state=42)
embedding_2d = reducer.fit_transform(embeddings)

print("Clustering with HDBSCAN...")
clusterer = hdbscan.HDBSCAN(min_cluster_size=5, min_samples=2, metric="euclidean")
labels = clusterer.fit_predict(embedding_2d)

df = pd.DataFrame({
    "id": meta_ids,
    "x": embedding_2d[:, 0],
    "y": embedding_2d[:, 1],
    "cluster": labels,
    "name": names,
    "rating": ratings,
    "categories": cats
})
df.to_csv(OUTPUT_CSV, index=False)
print(f" Saved to {OUTPUT_CSV}")

plt.figure(figsize=(10, 8))
palette = sns.color_palette("husl", len(np.unique(labels)))
sns.scatterplot(
    x="x", y="y", hue="cluster", palette=palette, data=df, s=25, linewidth=0, alpha=0.8
)
plt.title("VibeCheck Aesthetic Map (UMAP + HDBSCAN)")
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title="Cluster ID")
plt.tight_layout()
plt.savefig("vibe_map_preview.png")
print("Preview saved as vibe_map_preview.png")
