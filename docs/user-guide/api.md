# Internal API Examples

## For Developers and Researchers

These examples show how to use the VibeCheck internal API for experiments and analysis.

### Basic Usage
```python
from vibecheck import VibeCheckRecommender
from PIL import Image

# Initialize recommender
recommender = VibeCheckRecommender()

# Search by text
results = recommender.search_by_text("cozy cafe with plants", top_k=5)
for resto in results:
    print(f"{resto['name']}: {resto['similarity']:.2%} match")

# Search by image
img = Image.open("ideal_restaurant.jpg")
results = recommender.search_by_image(img, top_k=5)
for resto in results:
    print(resto['name'])

# Search with both
results = recommender.search_multimodal(
    text="cozy atmosphere",
    image=img,
    top_k=5
)
```

### Running Experiments
```python
# Evaluate text search quality
test_queries = [
    "cozy cafe with plants",
    "modern minimalist restaurant",
    "rustic farmhouse dining"
]

for query in test_queries:
    results = recommender.search_by_text(query, top_k=10)
    print(f"\nQuery: {query}")
    for resto in results[:3]:
        print(f"  {resto['name']} ({resto['similarity']:.2f})")
```

### Reproducibility

All experiments can be reproduced using the same model weights and FAISS index:
```python
# Exact reproduction
recommender = VibeCheckRecommender(
    db_path="restaurants.db",
    faiss_index_path="vibecheck_index.faiss",
    meta_ids_path="meta_ids.npy"
)

# Results will be identical
results = recommender.search_by_text("cozy cafe", top_k=5)
```
