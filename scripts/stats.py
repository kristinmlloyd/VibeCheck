"""
Generate Real Statistics for VibeCheck Discussion Document
===========================================================
Analyzes your actual data to produce metrics for the paper.
"""

import sqlite3
import numpy as np
import pandas as pd
from pathlib import Path
from collections import Counter
import json

# ==============================================================================
# CONFIG
# ==============================================================================

OUTPUT_DIR = Path("./vibecheck_full_output")
DB_PATH = OUTPUT_DIR / "vibecheck.db"
EMBEDDINGS_PATH = OUTPUT_DIR / "vibe_embeddings.npy"
VIBE_MAP_CSV = OUTPUT_DIR / "vibe_map.csv"

# ==============================================================================
# STATISTICS GENERATION
# ==============================================================================

def get_basic_stats():
    """Get basic dataset statistics."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    stats = {}
    
    # Total restaurants
    cursor.execute("SELECT COUNT(*) FROM restaurants")
    stats['total_restaurants'] = cursor.fetchone()[0]
    
    # Rating statistics
    cursor.execute("SELECT AVG(rating), MIN(rating), MAX(rating) FROM restaurants WHERE rating IS NOT NULL")
    avg_rating, min_rating, max_rating = cursor.fetchone()
    stats['avg_rating'] = round(avg_rating, 2) if avg_rating else 0
    stats['min_rating'] = min_rating if min_rating else 0
    stats['max_rating'] = max_rating if max_rating else 0
    
    # Rating median
    cursor.execute("SELECT rating FROM restaurants WHERE rating IS NOT NULL ORDER BY rating")
    ratings = [r[0] for r in cursor.fetchall()]
    stats['median_rating'] = round(np.median(ratings), 2) if ratings else 0
    
    # Review count statistics
    cursor.execute("SELECT AVG(reviews_count), MIN(reviews_count), MAX(reviews_count) FROM restaurants WHERE reviews_count IS NOT NULL")
    avg_reviews, min_reviews, max_reviews = cursor.fetchone()
    stats['avg_reviews'] = round(avg_reviews, 1) if avg_reviews else 0
    stats['min_reviews'] = min_reviews if min_reviews else 0
    stats['max_reviews'] = max_reviews if max_reviews else 0
    
    # Total reviews in database
    cursor.execute("SELECT COUNT(*) FROM reviews")
    stats['total_reviews'] = cursor.fetchone()[0]
    
    # Average review length
    cursor.execute("SELECT AVG(LENGTH(review_text)) FROM reviews WHERE review_text IS NOT NULL")
    result = cursor.fetchone()
    stats['avg_review_length'] = round(result[0], 0) if result and result[0] else 0
    
    # Total photos
    cursor.execute("SELECT COUNT(*) FROM vibe_photos")
    stats['total_photos'] = cursor.fetchone()[0]
    
    # Restaurants with photos
    cursor.execute("SELECT COUNT(DISTINCT restaurant_id) FROM vibe_photos WHERE local_filename IS NOT NULL")
    stats['restaurants_with_photos'] = cursor.fetchone()[0]
    
    # Average photos per restaurant
    cursor.execute("""
        SELECT AVG(photo_count) FROM (
            SELECT restaurant_id, COUNT(*) as photo_count 
            FROM vibe_photos 
            WHERE local_filename IS NOT NULL
            GROUP BY restaurant_id
        )
    """)
    result = cursor.fetchone()
    stats['avg_photos_per_restaurant'] = round(result[0], 1) if result and result[0] else 0
    
    conn.close()
    return stats


def get_vibe_distribution():
    """Get vibe category distribution."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT vibe_name, SUM(mention_count) as total
        FROM vibe_analysis
        GROUP BY vibe_name
        ORDER BY total DESC
    """)
    
    vibes = cursor.fetchall()
    total_mentions = sum(v[1] for v in vibes)
    
    vibe_stats = []
    for vibe_name, count in vibes:
        percentage = round((count / total_mentions * 100), 1) if total_mentions > 0 else 0
        vibe_stats.append({
            'name': vibe_name,
            'count': count,
            'percentage': percentage
        })
    
    conn.close()
    return vibe_stats


def get_cluster_stats():
    """Get clustering statistics."""
    if not VIBE_MAP_CSV.exists():
        return None
    
    df = pd.read_csv(VIBE_MAP_CSV)
    
    stats = {}
    stats['n_clusters'] = int(len(df[df['cluster'] != -1]['cluster'].unique()))
    stats['n_noise'] = int(len(df[df['cluster'] == -1]))
    stats['noise_percentage'] = round(float(stats['n_noise'] / len(df) * 100), 1)
    
    # Cluster sizes
    cluster_sizes = df[df['cluster'] != -1].groupby('cluster').size()
    stats['avg_cluster_size'] = round(float(cluster_sizes.mean()), 1)
    stats['min_cluster_size'] = int(cluster_sizes.min())
    stats['max_cluster_size'] = int(cluster_sizes.max())
    
    # Cluster ratings
    cluster_ratings = df[df['cluster'] != -1].groupby('cluster')['rating'].mean()
    stats['cluster_rating_range'] = f"{float(cluster_ratings.min()):.2f} - {float(cluster_ratings.max()):.2f}"
    
    return stats


def get_embedding_stats():
    """Get embedding space statistics."""
    if not EMBEDDINGS_PATH.exists():
        return None
    
    embeddings = np.load(EMBEDDINGS_PATH)
    
    stats = {}
    stats['n_embeddings'] = len(embeddings)
    stats['embedding_dim'] = embeddings.shape[1]
    stats['text_dim'] = 384
    stats['image_dim'] = 512
    
    # Compute pairwise similarities (sample for speed)
    sample_size = min(500, len(embeddings))
    sample_idx = np.random.choice(len(embeddings), sample_size, replace=False)
    sample_embeddings = embeddings[sample_idx]
    
    # Compute cosine similarities
    from sklearn.metrics.pairwise import cosine_similarity
    similarities = cosine_similarity(sample_embeddings)
    
    # Remove diagonal (self-similarities)
    mask = ~np.eye(similarities.shape[0], dtype=bool)
    similarities_no_diag = similarities[mask]
    
    stats['mean_similarity'] = round(float(np.mean(similarities_no_diag)), 3)
    stats['std_similarity'] = round(float(np.std(similarities_no_diag)), 3)
    stats['min_similarity'] = round(float(np.min(similarities_no_diag)), 3)
    stats['max_similarity'] = round(float(np.max(similarities_no_diag)), 3)
    
    return stats


def calculate_precision_at_k(k=5):
    """
    Calculate synthetic Precision@K based on vibe similarity.
    This is an approximation - real evaluation would need human labels.
    """
    conn = sqlite3.connect(DB_PATH)
    
    # Get restaurants with their dominant vibes
    query = """
        SELECT r.id, r.name, va.vibe_name, va.mention_count
        FROM restaurants r
        JOIN vibe_analysis va ON r.id = va.restaurant_id
        WHERE va.mention_count = (
            SELECT MAX(mention_count) 
            FROM vibe_analysis 
            WHERE restaurant_id = r.id
        )
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if len(df) < 10:
        return None
    
    # Load embeddings
    if not EMBEDDINGS_PATH.exists():
        return None
    
    embeddings = np.load(EMBEDDINGS_PATH)
    meta_ids = np.load(OUTPUT_DIR / "meta_ids.npy")
    
    # Create mapping
    id_to_idx = {int(rid): idx for idx, rid in enumerate(meta_ids)}
    
    # Sample test queries
    np.random.seed(42)
    test_sample = df.sample(min(50, len(df)))
    
    precisions = []
    
    for _, row in test_sample.iterrows():
        query_id = row['id']
        query_vibe = row['vibe_name']
        
        if query_id not in id_to_idx:
            continue
        
        query_idx = id_to_idx[query_id]
        query_emb = embeddings[query_idx:query_idx+1]
        
        # Compute similarities
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(query_emb, embeddings)[0]
        
        # Get top-k (excluding self)
        top_k_indices = np.argsort(similarities)[::-1][1:k+1]
        top_k_ids = [int(meta_ids[idx]) for idx in top_k_indices]
        
        # Check how many have same vibe
        matches = 0
        for top_id in top_k_ids:
            top_vibe = df[df['id'] == top_id]['vibe_name'].values
            if len(top_vibe) > 0 and top_vibe[0] == query_vibe:
                matches += 1
        
        precision = matches / k
        precisions.append(precision)
    
    return round(float(np.mean(precisions)), 2) if precisions else None


def generate_all_stats():
    """Generate all statistics and save to file."""
    print("\n" + "=" * 60)
    print("📊 GENERATING PROJECT STATISTICS")
    print("=" * 60)
    
    all_stats = {}
    
    # Basic stats
    print("\n1️⃣ Collecting basic dataset statistics...")
    all_stats['basic'] = get_basic_stats()
    
    # Vibe distribution
    print("2️⃣ Analyzing vibe distribution...")
    all_stats['vibes'] = get_vibe_distribution()
    
    # Cluster stats
    print("3️⃣ Computing cluster statistics...")
    all_stats['clusters'] = get_cluster_stats()
    
    # Embedding stats
    print("4️⃣ Analyzing embedding space...")
    all_stats['embeddings'] = get_embedding_stats()
    
    # Precision metrics
    print("5️⃣ Computing precision@k metrics...")
    all_stats['precision_at_5'] = calculate_precision_at_k(5)
    all_stats['precision_at_10'] = calculate_precision_at_k(10)
    
    # Save to file
    output_file = OUTPUT_DIR / "project_statistics.json"
    with open(output_file, 'w') as f:
        json.dump(all_stats, f, indent=2)
    
    print(f"\n💾 Saved to: {output_file}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("📈 STATISTICS SUMMARY")
    print("=" * 60)
    
    print(f"\n🍽️  Dataset Overview:")
    print(f"   Total restaurants: {all_stats['basic']['total_restaurants']}")
    print(f"   Total reviews: {all_stats['basic']['total_reviews']}")
    print(f"   Total photos: {all_stats['basic']['total_photos']}")
    print(f"   Restaurants with photos: {all_stats['basic']['restaurants_with_photos']}")
    
    print(f"\n⭐ Rating Statistics:")
    print(f"   Mean: {all_stats['basic']['avg_rating']}")
    print(f"   Median: {all_stats['basic']['median_rating']}")
    print(f"   Range: {all_stats['basic']['min_rating']} - {all_stats['basic']['max_rating']}")
    
    print(f"\n📝 Review Statistics:")
    print(f"   Avg reviews per restaurant: {all_stats['basic']['avg_reviews']}")
    print(f"   Review count range: {all_stats['basic']['min_reviews']} - {all_stats['basic']['max_reviews']}")
    print(f"   Avg review length: {all_stats['basic']['avg_review_length']} chars")
    
    print(f"\n✨ Top 5 Vibes:")
    for i, vibe in enumerate(all_stats['vibes'][:5], 1):
        print(f"   {i}. {vibe['name']}: {vibe['percentage']}% ({vibe['count']} mentions)")
    
    if all_stats['clusters']:
        print(f"\n🎯 Cluster Statistics:")
        print(f"   Number of clusters: {all_stats['clusters']['n_clusters']}")
        print(f"   Noise points: {all_stats['clusters']['n_noise']} ({all_stats['clusters']['noise_percentage']}%)")
        print(f"   Avg cluster size: {all_stats['clusters']['avg_cluster_size']}")
        print(f"   Cluster size range: {all_stats['clusters']['min_cluster_size']} - {all_stats['clusters']['max_cluster_size']}")
    
    if all_stats['embeddings']:
        print(f"\n🧠 Embedding Space:")
        print(f"   Dimension: {all_stats['embeddings']['embedding_dim']}")
        print(f"   Mean similarity: {all_stats['embeddings']['mean_similarity']}")
        print(f"   Similarity std: {all_stats['embeddings']['std_similarity']}")
    
    if all_stats['precision_at_5']:
        print(f"\n📊 Search Performance:")
        print(f"   Precision@5: {all_stats['precision_at_5']}")
        print(f"   Precision@10: {all_stats['precision_at_10']}")
    
    print("\n" + "=" * 60)
    print("✅ STATISTICS GENERATION COMPLETE")
    print("=" * 60)
    print(f"\n💡 Use these numbers in your discussion.md!")
    
    return all_stats


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    stats = generate_all_stats()