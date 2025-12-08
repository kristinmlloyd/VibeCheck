"""
VibeCheck Interactive Map Generator
====================================
Creates beautiful, interactive UMAP projections of restaurant vibes.
Generates multiple visualizations with Plotly for web viewing.
"""

import numpy as np
import pandas as pd
import sqlite3
import umap
import hdbscan
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import matplotlib
matplotlib.use("Agg")

# ==============================================================================
# CONFIG
# ==============================================================================

OUTPUT_DIR = Path("./vibecheck_full_output")
DB_PATH = OUTPUT_DIR / "vibecheck.db"
META_IDS_PATH = OUTPUT_DIR / "meta_ids.npy"
EMBEDDINGS_PATH = OUTPUT_DIR / "vibe_embeddings.npy"
OUTPUT_CSV = OUTPUT_DIR / "vibe_map.csv"

# Output files
STATIC_PNG = OUTPUT_DIR / "vibe_map_static.png"
INTERACTIVE_HTML = OUTPUT_DIR / "vibe_map_interactive.html"
CLUSTERS_HTML = OUTPUT_DIR / "vibe_clusters_detailed.html"
VIBES_HTML = OUTPUT_DIR / "vibe_distribution.html"

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("\n" + "=" * 60)
    print("🗺️  VIBECHECK INTERACTIVE MAP GENERATOR")
    print("=" * 60)
    
    # Check if embeddings exist
    if not EMBEDDINGS_PATH.exists():
        print(f"\n❌ Embeddings not found: {EMBEDDINGS_PATH}")
        print("   Run vibecheck_embeddings.py first!")
        return
    
    # Load embeddings and metadata
    print("\n📂 Loading embeddings...")
    embeddings = np.load(EMBEDDINGS_PATH)
    meta_ids = np.load(META_IDS_PATH)
    print(f"✅ Loaded {len(embeddings)} embeddings (dim: {embeddings.shape[1]})")
    
    # Load restaurant metadata from database
    print("\n📊 Loading restaurant metadata...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    names = []
    ratings = []
    addresses = []
    review_counts = []
    all_vibes = []
    photo_counts = []
    
    for restaurant_id in tqdm(meta_ids, desc="Fetching metadata"):
        # Get basic info
        cursor.execute("""
            SELECT name, rating, address, reviews_count
            FROM restaurants
            WHERE id = ?
        """, (int(restaurant_id),))
        
        row = cursor.fetchone()
        
        if row:
            name, rating, address, reviews_count = row
            names.append(name)
            ratings.append(rating if rating else 0)
            addresses.append(address or "")
            review_counts.append(reviews_count or 0)
            
            # Get ALL vibes for this restaurant
            cursor.execute("""
                SELECT vibe_name, mention_count
                FROM vibe_analysis
                WHERE restaurant_id = ?
                ORDER BY mention_count DESC
            """, (int(restaurant_id),))
            
            vibe_rows = cursor.fetchall()
            if vibe_rows:
                vibe_str = ", ".join([f"{v} ({c})" for v, c in vibe_rows[:3]])
                all_vibes.append(vibe_str)
            else:
                all_vibes.append("No vibes detected")
            
            # Count photos
            cursor.execute("""
                SELECT COUNT(*) FROM vibe_photos WHERE restaurant_id = ?
            """, (int(restaurant_id),))
            photo_count = cursor.fetchone()[0]
            photo_counts.append(photo_count)
        else:
            names.append("Unknown")
            ratings.append(0)
            addresses.append("")
            review_counts.append(0)
            all_vibes.append("Unknown")
            photo_counts.append(0)
    
    conn.close()
    print(f"✅ Loaded metadata for {len(names)} restaurants")
    
    # UMAP dimensionality reduction
    print("\n🔄 Running UMAP projection (2D)...")
    reducer = umap.UMAP(
        n_neighbors=15, 
        min_dist=0.1, 
        metric="cosine", 
        random_state=42,
        verbose=True
    )
    embedding_2d = reducer.fit_transform(embeddings)
    print("✅ UMAP projection complete")
    
    # HDBSCAN clustering
    print("\n🔍 Clustering with HDBSCAN...")
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=5, 
        min_samples=3, 
        metric="euclidean"
    )
    labels = clusterer.fit_predict(embedding_2d)
    
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = list(labels).count(-1)
    print(f"✅ Found {n_clusters} clusters ({n_noise} noise points)")
    
    # Create DataFrame
    df = pd.DataFrame({
        "id": meta_ids,
        "x": embedding_2d[:, 0],
        "y": embedding_2d[:, 1],
        "cluster": labels,
        "name": names,
        "rating": ratings,
        "address": addresses,
        "review_count": review_counts,
        "vibes": all_vibes,
        "photo_count": photo_counts
    })
    
    # Add cluster labels
    df['cluster_label'] = df['cluster'].apply(
        lambda x: f"Cluster {x}" if x != -1 else "Noise"
    )
    
    # Save CSV
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n💾 Saved map data to: {OUTPUT_CSV}")
    
    # =========================================================================
    # VISUALIZATION 1: Static Matplotlib (Beautiful Publication Quality)
    # =========================================================================
    print("\n🎨 Creating static visualization...")
    
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # Set style
    sns.set_style("whitegrid")
    plt.rcParams['font.family'] = 'sans-serif'
    
    # Create color palette
    unique_clusters = sorted(df['cluster'].unique())
    n_colors = len(unique_clusters)
    colors = sns.color_palette("husl", n_colors)
    cluster_colors = {c: colors[i] for i, c in enumerate(unique_clusters)}
    
    # Plot each cluster
    for cluster_id in unique_clusters:
        cluster_df = df[df['cluster'] == cluster_id]
        
        if cluster_id == -1:
            # Noise points - gray and smaller
            ax.scatter(
                cluster_df['x'], cluster_df['y'],
                c='lightgray', s=30, alpha=0.3, 
                edgecolors='white', linewidths=0.5,
                label='Unclustered', zorder=1
            )
        else:
            # Regular clusters
            ax.scatter(
                cluster_df['x'], cluster_df['y'],
                c=[cluster_colors[cluster_id]], s=100, alpha=0.7,
                edgecolors='white', linewidths=1,
                label=f'Cluster {cluster_id} (n={len(cluster_df)})',
                zorder=2
            )
    
    ax.set_title('VibeCheck: DC Restaurant Aesthetic Space', 
                 fontsize=20, fontweight='bold', pad=20)
    ax.set_xlabel('UMAP Dimension 1', fontsize=14)
    ax.set_ylabel('UMAP Dimension 2', fontsize=14)
    
    # Legend
    ax.legend(
        bbox_to_anchor=(1.05, 1), loc='upper left',
        frameon=True, fancybox=True, shadow=True,
        fontsize=10, title='Clusters', title_fontsize=12
    )
    
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_facecolor('#f8f9fa')
    fig.patch.set_facecolor('white')
    
    plt.tight_layout()
    plt.savefig(STATIC_PNG, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Saved static map: {STATIC_PNG}")
    plt.close()
    
    # =========================================================================
    # VISUALIZATION 2: Interactive Plotly Scatter (Main View)
    # =========================================================================
    print("\n🌟 Creating interactive scatter plot...")
    
    # Create hover text
    df['hover_text'] = df.apply(
        lambda row: f"<b>{row['name']}</b><br>" +
                    f"Rating: {row['rating']:.1f}⭐ ({row['review_count']} reviews)<br>" +
                    f"Vibes: {row['vibes']}<br>" +
                    f"Photos: {row['photo_count']}<br>" +
                    f"Address: {row['address'][:50]}",
        axis=1
    )
    
    fig = px.scatter(
        df[df['cluster'] != -1],  # Exclude noise for cleaner view
        x='x', y='y',
        color='cluster_label',
        size='rating',
        hover_data={'hover_text': True, 'x': False, 'y': False, 
                    'cluster_label': False, 'rating': False},
        color_discrete_sequence=px.colors.qualitative.Bold,
        title='🍽️ DC Restaurant Vibe Map - Interactive Explorer',
        labels={'x': 'Aesthetic Dimension 1', 'y': 'Aesthetic Dimension 2'}
    )
    
    fig.update_traces(
        marker=dict(line=dict(width=1, color='white')),
        hovertemplate='%{customdata[0]}<extra></extra>'
    )
    
    fig.update_layout(
        template='plotly_white',
        width=1400,
        height=900,
        font=dict(size=12, family='Arial'),
        title=dict(font=dict(size=20, color='#2c3e50')),
        hovermode='closest',
        plot_bgcolor='rgba(245,245,245,0.5)',
        showlegend=True,
        legend=dict(
            title=dict(text='Restaurant Clusters', font=dict(size=14)),
            orientation='v',
            x=1.02,
            y=1
        )
    )
    
    fig.write_html(INTERACTIVE_HTML)
    print(f"✅ Saved interactive map: {INTERACTIVE_HTML}")
    
    # =========================================================================
    # VISUALIZATION 3: Cluster Analysis Dashboard
    # =========================================================================
    print("\n📊 Creating cluster analysis dashboard...")
    
    # Prepare cluster statistics
    cluster_stats = []
    for cluster_id in sorted(df['cluster'].unique()):
        if cluster_id == -1:
            continue
        cluster_df = df[df['cluster'] == cluster_id]
        
        cluster_stats.append({
            'Cluster': f'Cluster {cluster_id}',
            'Size': len(cluster_df),
            'Avg Rating': cluster_df['rating'].mean(),
            'Avg Reviews': cluster_df['review_count'].mean(),
            'Avg Photos': cluster_df['photo_count'].mean()
        })
    
    cluster_stats_df = pd.DataFrame(cluster_stats)
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Cluster Sizes', 
            'Average Rating by Cluster',
            'Average Reviews by Cluster',
            'Average Photos by Cluster'
        ),
        specs=[[{'type': 'bar'}, {'type': 'bar'}],
               [{'type': 'bar'}, {'type': 'bar'}]]
    )
    
    # Cluster sizes
    fig.add_trace(
        go.Bar(
            x=cluster_stats_df['Cluster'],
            y=cluster_stats_df['Size'],
            marker_color='lightblue',
            name='Size'
        ),
        row=1, col=1
    )
    
    # Average rating
    fig.add_trace(
        go.Bar(
            x=cluster_stats_df['Cluster'],
            y=cluster_stats_df['Avg Rating'],
            marker_color='gold',
            name='Avg Rating'
        ),
        row=1, col=2
    )
    
    # Average reviews
    fig.add_trace(
        go.Bar(
            x=cluster_stats_df['Cluster'],
            y=cluster_stats_df['Avg Reviews'],
            marker_color='lightcoral',
            name='Avg Reviews'
        ),
        row=2, col=1
    )
    
    # Average photos
    fig.add_trace(
        go.Bar(
            x=cluster_stats_df['Cluster'],
            y=cluster_stats_df['Avg Photos'],
            marker_color='lightgreen',
            name='Avg Photos'
        ),
        row=2, col=2
    )
    
    fig.update_layout(
        title_text='📈 Cluster Analysis Dashboard',
        title_font_size=20,
        showlegend=False,
        height=800,
        template='plotly_white'
    )
    
    fig.write_html(CLUSTERS_HTML)
    print(f"✅ Saved cluster dashboard: {CLUSTERS_HTML}")
    
    # =========================================================================
    # VISUALIZATION 4: Vibe Distribution Analysis
    # =========================================================================
    print("\n✨ Creating vibe distribution visualization...")
    
    # Extract top vibes across all restaurants
    conn = sqlite3.connect(DB_PATH)
    vibe_df = pd.read_sql_query("""
        SELECT vibe_name, SUM(mention_count) as total_mentions
        FROM vibe_analysis
        GROUP BY vibe_name
        ORDER BY total_mentions DESC
        LIMIT 10
    """, conn)
    conn.close()
    
    if not vibe_df.empty:
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=vibe_df['vibe_name'],
            y=vibe_df['total_mentions'],
            marker=dict(
                color=vibe_df['total_mentions'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Mentions")
            ),
            text=vibe_df['total_mentions'],
            textposition='outside'
        ))
        
        fig.update_layout(
            title='🎭 Top 10 Vibes Across DC Restaurants',
            title_font_size=20,
            xaxis_title='Vibe Category',
            yaxis_title='Total Mentions',
            template='plotly_white',
            height=600,
            font=dict(size=12)
        )
        
        fig.write_html(VIBES_HTML)
        print(f"✅ Saved vibe distribution: {VIBES_HTML}")
    
    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    print("\n" + "=" * 60)
    print("📊 CLUSTER STATISTICS")
    print("=" * 60)
    
    for cluster_id in sorted(df['cluster'].unique()):
        cluster_df = df[df['cluster'] == cluster_id]
        
        if cluster_id == -1:
            print(f"\n🔸 Noise Points: {len(cluster_df)}")
        else:
            print(f"\n🔹 Cluster {cluster_id}: {len(cluster_df)} restaurants")
            
            # Average stats
            avg_rating = cluster_df['rating'].mean()
            avg_reviews = cluster_df['review_count'].mean()
            avg_photos = cluster_df['photo_count'].mean()
            
            print(f"   Avg rating: {avg_rating:.2f}⭐")
            print(f"   Avg reviews: {avg_reviews:.1f}")
            print(f"   Avg photos: {avg_photos:.1f}")
            
            # Sample restaurants
            top_rated = cluster_df.nlargest(3, 'rating')[['name', 'rating']].values
            print(f"   Top rated:")
            for name, rating in top_rated:
                print(f"      • {name} ({rating:.1f}⭐)")
    
    print("\n" + "=" * 60)
    print("✅ MAP GENERATION COMPLETE")
    print("=" * 60)
    print(f"📊 Total restaurants: {len(df)}")
    print(f"🎯 Clusters found: {n_clusters}")
    print(f"\n📁 Output files:")
    print(f"   📄 Data: {OUTPUT_CSV}")
    print(f"   🖼️  Static: {STATIC_PNG}")
    print(f"   🌐 Interactive map: {INTERACTIVE_HTML}")
    print(f"   📊 Cluster dashboard: {CLUSTERS_HTML}")
    print(f"   ✨ Vibe distribution: {VIBES_HTML}")
    print(f"\n💡 Open the HTML files in your browser for interactive exploration!")


if __name__ == "__main__":
    main()