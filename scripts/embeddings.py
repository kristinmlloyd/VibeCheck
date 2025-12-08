"""
VibeCheck Embeddings Generator
===============================
Creates embeddings from restaurant reviews and vibe photos.
Uses SentenceTransformer for text and CLIP for images.
Handles multiple reviews and images per restaurant.
"""

import os
import sqlite3
import numpy as np
import torch
import clip
from PIL import Image
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import faiss
from pathlib import Path

# ==============================================================================
# CONFIG
# ==============================================================================

OUTPUT_DIR = Path("./vibecheck_full_output")
DB_PATH = OUTPUT_DIR / "vibecheck.db"
IMAGE_DIR = OUTPUT_DIR / "images"
FAISS_PATH = OUTPUT_DIR / "vibecheck_index.faiss"
META_IDS_PATH = OUTPUT_DIR / "meta_ids.npy"
EMBEDDINGS_PATH = OUTPUT_DIR / "vibe_embeddings.npy"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# How many images to use per restaurant (average their embeddings)
MAX_IMAGES_PER_RESTAURANT = 5

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("\n" + "=" * 60)
    print("🧠 VIBECHECK EMBEDDINGS GENERATOR")
    print("=" * 60)
    print(f"Device: {DEVICE}")
    
    # Check if database exists
    if not DB_PATH.exists():
        print(f"\n❌ Database not found: {DB_PATH}")
        print("   Run load_vibecheck_to_sql.py first!")
        return
    
    # Load models
    print("\n📦 Loading models...")
    print("   - SentenceTransformer for text...")
    text_model = SentenceTransformer("all-MiniLM-L6-v2", device=DEVICE)
    print("   - CLIP for images...")
    clip_model, clip_preprocess = clip.load("ViT-B/32", device=DEVICE)
    print("✅ Models loaded")
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all restaurants
    print("\n📊 Loading restaurant data...")
    cursor.execute("SELECT id, name, place_id FROM restaurants")
    restaurants = cursor.fetchall()
    print(f"✅ Loaded {len(restaurants)} restaurants")
    
    # Generate embeddings
    embeddings = []
    meta_ids = []
    
    print("\n🔄 Generating embeddings...")
    for restaurant_id, name, place_id in tqdm(restaurants, desc="Processing"):
        
        # ============ TEXT EMBEDDING ============
        # Get ALL reviews for this restaurant and combine them
        cursor.execute("""
            SELECT review_text 
            FROM reviews 
            WHERE restaurant_id = ?
        """, (restaurant_id,))
        
        review_rows = cursor.fetchall()
        
        if review_rows:
            # Combine all reviews with spaces
            all_review_text = " ".join([r[0] for r in review_rows if r[0]])
            text_content = all_review_text
        else:
            # Fallback to restaurant name if no reviews
            text_content = name or ""
        
        # Generate text embedding
        text_vec = text_model.encode(
            text_content, 
            convert_to_numpy=True, 
            normalize_embeddings=True
        )
        
        # ============ IMAGE EMBEDDING ============
        # Get ALL vibe photos for this restaurant
        cursor.execute("""
            SELECT local_filename 
            FROM vibe_photos 
            WHERE restaurant_id = ? AND local_filename IS NOT NULL
            LIMIT ?
        """, (restaurant_id, MAX_IMAGES_PER_RESTAURANT))
        
        photo_rows = cursor.fetchall()
        
        if photo_rows:
            # Process multiple images and average their embeddings
            img_vecs = []
            
            for (filename,) in photo_rows:
                img_path = IMAGE_DIR / filename
                
                if img_path.exists():
                    try:
                        image = clip_preprocess(Image.open(img_path)).unsqueeze(0).to(DEVICE)
                        with torch.no_grad():
                            img_vec = clip_model.encode_image(image)
                        img_vec /= img_vec.norm(dim=-1, keepdim=True)
                        img_vec = img_vec.cpu().numpy()[0]
                        img_vecs.append(img_vec)
                    except Exception as e:
                        # Skip images that fail to load
                        continue
            
            if img_vecs:
                # Average all image embeddings
                img_vec = np.mean(img_vecs, axis=0).astype("float32")
                # Renormalize after averaging
                img_vec = img_vec / np.linalg.norm(img_vec)
            else:
                # No valid images found
                img_vec = np.zeros((512,), dtype="float32")
        else:
            # No images in database
            img_vec = np.zeros((512,), dtype="float32")
        
        # ============ COMBINE EMBEDDINGS ============
        combined = np.concatenate([text_vec, img_vec]).astype("float32")
        embeddings.append(combined)
        meta_ids.append(restaurant_id)
    
    conn.close()
    
    # Stack embeddings
    embeddings = np.vstack(embeddings).astype("float32")
    print(f"\n✅ Generated {len(embeddings)} embeddings")
    print(f"   Dimension: {embeddings.shape[1]} (text: 384 + image: 512)")
    
    # Create FAISS index
    print("\n🔍 Building FAISS index...")
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # Inner product (cosine similarity)
    index.add(embeddings)
    
    # Save everything
    print("\n💾 Saving files...")
    faiss.write_index(index, str(FAISS_PATH))
    print(f"   ✅ FAISS index: {FAISS_PATH}")
    
    np.save(META_IDS_PATH, np.array(meta_ids))
    print(f"   ✅ Meta IDs: {META_IDS_PATH}")
    
    np.save(EMBEDDINGS_PATH, embeddings)
    print(f"   ✅ Embeddings: {EMBEDDINGS_PATH}")
    
    # Print statistics
    print("\n" + "=" * 60)
    print("📊 EMBEDDING STATISTICS")
    print("=" * 60)
    
    # Count restaurants with/without images
    cursor = sqlite3.connect(DB_PATH).cursor()
    cursor.execute("""
        SELECT COUNT(DISTINCT restaurant_id) 
        FROM vibe_photos 
        WHERE local_filename IS NOT NULL
    """)
    restaurants_with_images = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM reviews")
    total_reviews = cursor.fetchone()[0]
    
    cursor.close()
    
    print(f"🍽️  Total restaurants: {len(meta_ids)}")
    print(f"📷 Restaurants with images: {restaurants_with_images}")
    print(f"📝 Total reviews processed: {total_reviews}")
    print(f"📐 Embedding dimension: {dim}")
    
    print("\n" + "=" * 60)
    print("✅ EMBEDDINGS GENERATION COMPLETE")
    print("=" * 60)
    print(f"\nNext step: Run vibecheck_maps.py to generate visualization")


if __name__ == "__main__":
    main()