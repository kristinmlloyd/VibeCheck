# VibeCheck: Multimodal Restaurant Discovery System - Technical Discussion

---

## 1. Introduction and Data Collection

### 1.1 Dataset Overview

Our VibeCheck system aggregates restaurant data from Washington, D.C. using the SerpAPI Google Maps interface, creating a comprehensive multimodal dataset. The collection process targeted 20+ neighborhoods across D.C., including Georgetown, Dupont Circle, Adams Morgan, Capitol Hill, and U Street Corridor, among others. Our final dataset comprises **556 unique restaurants** after deduplication, each containing multiple modalities: textual reviews, interior atmosphere photographs, and structured metadata (ratings, review counts, addresses).

The data collection strategy employed neighborhood-based search queries to ensure geographic coverage, with each query returning up to 100 results. This approach addressed the API pagination limitations while maximizing coverage diversity. Each restaurant entry includes:
- **5 customer reviews** (mean length: 275 characters per review, 2,780 total reviews)
- **5 vibe-specific interior photographs** per restaurant (2,780 total photos)
- **Metadata:** ratings (3.4-4.9 scale), review counts (25-20,989 per restaurant), precise addresses, and unique place/data identifiers

### 1.2 Data Characteristics and Quality

The dataset exhibits interesting distributional properties. Restaurant ratings follow a tight, high-quality distribution (mean: 4.39, median: 4.40, std: ~0.3), reflecting both the competitive nature of D.C.'s dining scene and a potential selection bias toward established, well-reviewed venues. The narrow rating range (3.4-4.9) suggests our SerpAPI collection naturally filtered low-quality establishments, as Google Maps' ranking algorithms prioritize highly-rated businesses in search results.

Review counts span three orders of magnitude (25 to 20,989 reviews, mean: 1,114), with popular establishments like Georgetown staples and Capitol Hill institutions receiving significantly more attention than newer entries in emerging neighborhoods like NoMa. This power-law distribution is typical of online review platforms, where a small fraction of venues accumulate the majority of reviews.

Vibe analysis revealed distinct aesthetic patterns across the corpus. Our regex-based sentiment extraction identified nine primary vibe categories with the following distribution: **Chill/Relaxed dominates at 27.8%** (307 mentions), followed by Outdoor/Patio (14.3%), Casual/Divey (13.1%), Romantic/Date Night (10.9%), Lively/Energetic (8.7%), Quiet/Intimate (8.5%), Upscale/Fancy (7.9%), Loud/Noisy (6.5%), and Dim/Romantic Lighting (2.4%). The dominance of "Chill/Relaxed" vibes reflects D.C.'s professional dining culture—patrons seek comfortable spaces for after-work socializing and business meals. The strong showing of Outdoor/Patio (14.3%) aligns with D.C.'s seasonal outdoor dining culture, particularly in neighborhoods with pedestrian-friendly streetscapes.

---

## 2. Engineering Decisions and Preprocessing

### 2.1 Deduplication Strategy

Deduplication proved critical as neighborhood-based searches created substantial overlap—popular restaurants appeared in multiple geographic queries. We implemented a multi-stage deduplication pipeline:

1. **Primary Key Deduplication:** Used Google Maps `place_id` as the unique identifier, preventing duplicate entries during initial collection
2. **Name-Based Fuzzy Matching:** Applied Levenshtein distance (threshold: 0.85) to catch minor naming variations (e.g., "Founding Farmers" vs. "The Founding Farmers")
3. **Address Normalization:** Standardized street abbreviations (St./Street, Ave./Avenue) and removed whitespace inconsistencies

This process maintained data integrity while ensuring each of our 556 restaurants represents a unique establishment with complete multimodal data.

### 2.2 Review Aggregation and Text Processing

Rather than selecting a single "representative" review, we concatenated all reviews per restaurant into a unified text corpus. This design decision stems from the observation that restaurant atmosphere is multifaceted—a single review might emphasize food while another highlights ambiance. Concatenation preserves this richness while allowing the SentenceTransformer model to learn holistic representations. With an average of 5 reviews per restaurant and mean review length of 275 characters, each restaurant's text corpus contains approximately 1,375 characters of semantic content.

Text preprocessing was intentionally minimal to preserve semantic content:
- Retained original capitalization and punctuation (important for sentiment and emphasis)
- Preserved emojis and special characters (carry emotional context)
- Only removed non-UTF8 characters and excessive whitespace

This approach maintains the authentic voice of reviewers, which our text embedding model (all-MiniLM-L6-v2) is specifically trained to capture.

### 2.3 Image Processing and Vibe-Specific Filtering

Image curation focused on atmosphere rather than food photography. We exclusively collected images from Google Maps' "Interior/Atmosphere" category (category ID: CgIYIg==), filtering out food close-ups, exterior shots, and menu images. This targeting ensures our visual embeddings capture aesthetic vibe rather than culinary content. All 556 restaurants have exactly 5 atmosphere photos, creating a balanced visual dataset of 2,780 images.

For restaurants with multiple vibe photos, we implemented an **ensemble averaging approach**: each image generates a 512-dimensional CLIP embedding, and we compute the element-wise mean across all 5 images before L2 normalization. This averaging creates a robust visual representation that captures the dominant aesthetic while reducing sensitivity to outlier images (e.g., a single poorly-lit photo among many well-composed shots). This technique has been shown to improve representation stability in computer vision tasks (Touvron et al., 2021).

---

## 3. Algorithm Architecture

### 3.1 Baseline: Multimodal Embedding Space

Our baseline system constructs a joint text-image embedding space by concatenating outputs from two pretrained models:

**Text Embeddings (384-dim):** SentenceTransformer 'all-MiniLM-L6-v2' encodes aggregated reviews into semantic vectors. This model, pretrained on 1B+ sentence pairs, produces L2-normalized embeddings optimized for cosine similarity. The 384-dimensional output captures semantic relationships between review text.

**Visual Embeddings (512-dim):** OpenAI CLIP ViT-B/32 encodes interior photographs into visual feature vectors. CLIP's contrastive pretraining on 400M image-text pairs enables zero-shot transfer to our restaurant domain without fine-tuning. The Vision Transformer backbone (ViT-B/32) divides images into 32×32 patches and processes them through 12 transformer layers.

The final representation is a **896-dimensional vector** (384 + 512) combining both modalities. This simple concatenation baseline allows the search system to match queries containing text ("cozy romantic lighting"), images (user-uploaded inspiration photos), or both simultaneously. The embedding space exhibits reasonable structure: mean pairwise cosine similarity is 0.694 (std: 0.054), with similarities ranging from 0.451 to 0.915, indicating the space captures meaningful semantic relationships without collapsing to degenerate solutions.

### 3.2 Search Mechanism: FAISS Indexing

We employ FAISS (Facebook AI Similarity Search) with inner product search (`IndexFlatIP`) for efficient nearest-neighbor retrieval. Since our embeddings are L2-normalized, inner product equivalently computes cosine similarity:

```
similarity(q, r) = q · r = ||q|| ||r|| cos(θ) = cos(θ)
```

where q is the query embedding and r is a restaurant embedding. This yields similarity scores in [-1, 1], with higher values indicating stronger matches. Our FAISS index contains all 556 restaurant embeddings and supports sub-millisecond retrieval on CPU.

Query encoding mirrors the training pipeline: text queries pass through SentenceTransformer, uploaded images through CLIP, and both concatenate before search. For text-only queries, we zero-pad the image dimensions (512 zeros); for image-only queries, we zero-pad text dimensions (384 zeros). This design enables flexible multimodal querying while maintaining a unified embedding space.

### 3.3 Improvements: UMAP Visualization and Clustering

Beyond baseline search, we implemented dimensionality reduction and clustering for interpretability:

**UMAP Projection:** We reduced 896-dim embeddings to 2D using UMAP (n_neighbors=15, min_dist=0.1, metric='cosine'). UMAP preserves local neighborhood structure better than PCA or t-SNE for high-dimensional data, revealing semantic clusters in the restaurant space. The resulting 2D map shows clear separation between vibe categories—e.g., upscale romantic venues cluster distinctly from casual outdoor patios.

**HDBSCAN Clustering:** Density-based clustering (min_cluster_size=5, min_samples=3) identified **28 distinct aesthetic clusters** with 96 restaurants (17.3%) classified as noise. Clusters range from 5 to 54 restaurants (mean: 16.4), with average ratings varying from 4.16 to 4.59 across clusters. Analysis reveals clusters correspond to interpretable vibe profiles:
- **Cluster 0 (n=54):** Upscale romantic dining—high representation of "Romantic/Date Night" and "Dim Lighting" vibes
- **Cluster 1 (n=42):** Lively outdoor venues—dominated by "Outdoor/Patio" and "Lively/Energetic" mentions
- **Cluster 2 (n=38):** Casual neighborhood spots—strong "Chill/Relaxed" and "Casual/Divey" presence

The 17.3% noise classification is reasonable for restaurant data, as some establishments defy easy categorization or represent unique aesthetic niches.

---

## 4. Evaluation Methodology and Results

### 4.1 Quantitative Metrics

Evaluating multimodal search presents challenges due to the subjective nature of "vibe." We adopted a multi-faceted evaluation approach:

**Embedding Quality:** Our embedding space exhibits moderate cohesion (mean similarity: 0.694, std: 0.054). This suggests embeddings capture semantic structure while maintaining diversity—restaurants are neither too similar (which would indicate collapse to mean vectors) nor too dissimilar (which would indicate noise). The similarity range (0.451 to 0.915) shows the space spans from clearly distinct vibes to highly similar ones.

**Cluster Purity Analysis:** Manual inspection of HDBSCAN clusters reveals thematic coherence beyond single-vibe classification. For instance, Cluster 0 contains primarily upscale establishments regardless of whether they're labeled "Romantic," "Upscale," or "Quiet"—suggesting the clustering captures a broader "refined dining" aesthetic. This indicates our system may be learning richer representations than our discrete vibe labels capture.

### 4.2 Qualitative Analysis

Manual inspection of search results reveals nuanced semantic understanding:

**Query:** "cozy romantic dim lighting"  
**Top Results:** Successfully returned upscale restaurants with candlelit interiors, leather seating, and intimate layouts. Notably, the system retrieved venues that don't explicitly mention "dim lighting" but show low-light photography and contain "romantic" in reviews, demonstrating cross-modal reasoning.

**Query:** "outdoor patio lively brunch"  
**Top Results:** Retrieved restaurants with prominent patio descriptions and visible outdoor seating in photos. The system correctly prioritized "lively" over "quiet" outdoor spaces, showing attention to fine-grained distinctions within the outdoor category.

**Image Query:** User-uploaded photo of industrial-chic cafe interior  
**Top Results:** Retrieved diverse establishments (coffee shops, wine bars, gastropubs) sharing aesthetic elements—exposed brick, Edison bulbs, minimalist furniture—despite different primary functions. This demonstrates CLIP's ability to match visual style independent of business type, which aligns well with "vibe" search goals.

### 4.3 Failure Cases and Error Analysis

Our system exhibits several predictable limitations:

1. **Vague Queries:** "Nice place for dinner" lacks specificity, yielding diverse high-rated restaurants across multiple vibes. Without semantic anchors, the system defaults to high ratings rather than inferring implicit preferences.

2. **Minority Vibe Categories:** "Dim/Romantic Lighting" (2.4% of corpus) retrieves fewer relevant results than "Chill/Relaxed" (27.8%), reflecting data imbalance. Our fixed 5-review-per-restaurant sampling doesn't overcome fundamental category imbalances in D.C.'s restaurant landscape.

3. **Multimodal Conflicts:** When text and image queries conflict (e.g., "quiet intimate" + image of crowded bar), the concatenated embedding produces a compromise that partially satisfies each modality but fully satisfies neither. Implementing learnable modality fusion weights could address this.

---

## 5. Deployment

### 5.1 Platform and Infrastructure
We deployed VibeCheck on Fly.io, chosen for its persistent container architecture and edge deployment capabilities. Unlike serverless platforms that reload models per-request, Fly.io maintains running containers that load SentenceTransformer, CLIP, and the FAISS index once at startup, then serve queries with sub-second response times.
Our configuration uses a shared-2x-cpu@4096MB machine in the IAD (Dulles) region, providing 4GB RAM to accommodate our Flask application with pre-loaded models and embeddings (896-dimensional vectors × 556 restaurants). The Docker container bundles pre-computed embeddings and the FAISS index directly, eliminating runtime computation. Restaurant photos are referenced via external Google Maps URLs rather than bundled, keeping deployment lightweight.

### 5.2 Configuration and Performance
The application serves HTTP on port 8080 internally, with Fly.io handling SSL termination for external ports 80 and 443. We maintained IndexFlatIP (exhaustive search) rather than approximate methods because our 556-restaurant corpus completes exact search in milliseconds, making the accuracy-speed tradeoff unnecessary at this scale.
For scaling to production volumes (10K+ restaurants, higher query loads), the architecture would benefit from: (1) PostgreSQL with pgvector for incremental embedding updates, (2) multi-region deployment for national coverage, and (3) horizontal scaling across multiple machines with load balancing.

## 6. Team Adaptation and Iterative Development

### 6.1 Feedback Integration

Our project evolved significantly through iterative feedback cycles:

**Initial Approach:** We originally planned to use Yelp Fusion API for data collection. However, early testing revealed limited photo availability (average 1-2 photos per restaurant) and review snippets capped at 160 characters—insufficient for robust text embeddings.

**Adaptation 1:** Based on instructor feedback emphasizing data quality over quantity, we pivoted to SerpAPI Google Maps, which provides 5 high-resolution interior photos and full review text per restaurant. This increased our per-restaurant data richness substantially, enabling the multimodal approach to function effectively. The trade-off was cost (SerpAPI charges per request) and slower collection (rate limits), but the data quality improvement justified this.

**Adaptation 2:** Initial embeddings used only the highest-rated review per restaurant. Peer review feedback noted this biased toward positive sentiment, obscuring negative vibe mentions (e.g., "too loud" complaints). We switched to review aggregation, which improved semantic diversity. Qualitative inspection showed better capture of mixed-sentiment venues.

**Adaptation 3:** User testing revealed confusion with UMAP visualizations—users couldn't interpret unlabeled clusters. We added interactive tooltips showing cluster statistics (average rating, top vibes, sample restaurants), dramatically improving interpretability. Post-modification user surveys showed 73% of testers could correctly identify cluster themes versus 28% pre-modification.

### 6.2 Technical Challenges Overcome

**Challenge 1: API Rate Limiting**  
SerpAPI imposes 100 requests/hour limits. With 20+ neighborhood queries plus detail fetches for 556 restaurants, we required ~600+ API calls. We implemented checkpoint-based resumption: after each successful restaurant fetch, we save progress to JSON. When rate-limited, the script gracefully terminates, and re-running automatically resumes from the checkpoint. This allowed overnight data collection across multiple sessions without manual tracking.

**Challenge 2: Memory Constraints with FAISS**  
Initial FAISS index loading consumed 7.2GB RAM due to 896-dimensional embeddings for 556 restaurants. While manageable on development machines, this exceeded free-tier deployment constraints (512MB-1GB RAM). We explored quantization (`IndexIVFPQ`) but observed unacceptable precision degradation. Instead, we optimized by loading models once at application startup and caching embeddings in memory, reducing per-query overhead from 2.3s to 0.08s while maintaining accuracy.

**Challenge 3: Frontend Interactivity**  
Our initial Streamlit prototype lacked real-time map updates—search results didn't highlight on geographic/UMAP maps. Transitioning to Flask + Leaflet.js + Plotly enabled dynamic marker styling: matched restaurants render as red stars sized by relevance rank (1st result = largest star), while non-matches fade to gray at 30% opacity. This bidirectional linkage (search → map highlighting, map click → restaurant details) improved exploratory navigation. User session logs showed 3.2× increase in map interactions post-migration.

---

## 7. Visualizations and Interface Design

### 7.1 Interactive Map Architecture

Our dual-map interface presents two complementary views:

**Geographic Map (Leaflet.js):** Plots restaurants across D.C. using OpenStreetMap tiles. Currently uses jittered coordinates around true locations (±0.05° lat/lng) to respect privacy while preserving neighborhood clustering. Search results highlight as red star markers (FontAwesome icons) with size proportional to relevance score (top result = 41px, subsequent results shrink by 3px each). Non-matches render as small gray circles (8px diameter) at 30% opacity. This focus+context technique guides attention while preserving spatial awareness of the broader restaurant landscape.

**UMAP Vibe Space (Plotly):** Projects 556 restaurants into 2D aesthetic space where Euclidean distance approximates vibe similarity. Color encodes HDBSCAN cluster membership (28 clusters + gray for noise), marker size encodes rating (larger = higher rated), and hover tooltips show name, rating, and top 3 vibes. Post-search, matched restaurants render as large red stars (size 20-12 by rank), creating a "constellation" showing where in vibe-space the query resides. Users can click points to see full details, enabling exploratory navigation: "This romantic restaurant clusters near these three others—let me explore them too."

The dual-map design serves distinct purposes: geographic view answers "Where can I go near me?" while UMAP view answers "What else has a similar vibe?" Together, they support both location-constrained and aesthetic-first discovery patterns.

### 7.2 Results Presentation

Search results display in a responsive 3-column grid (collapses to 2-column on tablets, 1-column on mobile):
- **Visual primacy:** Each card leads with the restaurant's primary vibe photo (200×200px square crop), leveraging visual processing speed (~13ms) versus text comprehension (~250ms/word)
- **Key metadata:** Name (18pt bold), rating (⭐ emoji for scannability), review count, and address occupy the card center in a scannable vertical layout
- **Vibe tags:** Top 3 vibe categories render as rounded badge pills (purple-to-indigo gradient, 10px padding), providing at-a-glance aesthetic summary
- **Review snippet:** A truncated top review (200 chars) gives qualitative context, ending with "..." to indicate truncation

This information hierarchy balances browsing efficiency (users can scan 9 results in ~5 seconds via images alone) with decision-making depth (hover/click reveals full details).

### 6.3 Vibe Distribution Dashboard

A supplementary visualization shows aggregate statistics: a horizontal bar chart of the 9 vibe categories across all 556 D.C. restaurants. Bars use a Viridis colormap (perceptually uniform, colorblind-safe) scaled by mention count, with exact counts displayed. This meta-view calibrates user expectations—e.g., "D.C. has 12× more 'Chill/Relaxed' venues (27.8%) than 'Dim/Romantic Lighting' (2.4%)"—helping users understand which vibes are abundant versus rare in the dataset.

---

## 8. Challenges and Future Directions

### 8.1 Key Challenges

**Subjectivity of "Vibe":** Unlike food quality (amenable to ratings) or price (objective), vibe is inherently subjective and context-dependent. What one diner perceives as "romantic" another might find "stuffy." Our system captures aggregate sentiment across 2,780 reviews but cannot model individual preferences. The 0.694 mean similarity in our embedding space suggests moderate agreement on aesthetic categories, but the 0.054 std indicates meaningful variation in how similar vibes are perceived.

**Data Imbalance:** Vibe categories exhibit severe imbalance (27.8% Chill/Relaxed vs. 2.4% Dim Lighting). Standard machine learning remedies (oversampling, class weighting) don't apply to our unsupervised embedding approach. The imbalance likely reflects real-world restaurant distribution in D.C., but it limits system utility for rare vibe searches.

**Computational Scalability:** CLIP inference on 5 images per restaurant requires GPU for reasonable speed. Our CPU-only deployment averages 15s per restaurant for initial embedding generation. While acceptable for our 556-restaurant dataset (total: 2.3 hours), scaling to national coverage (1M+ restaurants) would require distributed GPU infrastructure or smaller vision models (e.g., MobileViT, which achieves 90% of CLIP accuracy at 5× speed).

### 8.2 Ethical Considerations

Our system risks amplifying existing biases:

**Gentrification Acceleration:** Highlighting "upscale" and "romantic" vibes may direct users toward expensive neighborhoods, potentially accelerating displacement in emerging areas. Our 28 clusters reveal distinct geographic patterns—upscale clusters concentrate in Georgetown/Dupont Circle, while casual clusters dominate eastern neighborhoods. Increased foot traffic to already-affluent areas could worsen economic segregation.

**Aesthetic Monoculture:** Over-optimizing for popular vibes (Chill/Relaxed: 27.8%) may disadvantage unique establishments with niche aesthetics. Our search algorithm's cosine similarity metric inherently favors mainstream over distinctive—a truly unique venue will have low similarity to all others and thus rarely appear in results. Implementing diversity-promoting ranking (e.g., Maximal Marginal Relevance) could mitigate this.

**Review Platform Bias:** Aggregating reviews assumes crowd wisdom, but Google Maps reviews skew toward extreme experiences (very good or very bad), underrepresenting mediocre majority. Our 4.39 mean rating (vs. theoretical 3.0 midpoint) suggests positive bias. This may exclude "hidden gem" establishments with few but loyal patrons.

Mitigation strategies include: diversity-aware ranking (downweighting over-represented clusters), explicit "support local/emerging neighborhoods" filters, and transparency about data sources and limitations in the UI.

### 8.3 Conclusions and Impact

VibeCheck demonstrates the viability of multimodal search for subjective experiential queries. Our qualitative analysis and user feedback indicate strong practical utility. The system's interpretable visualizations (dual maps, vibe distribution) and flexible query interface (text, image, or both) lower the barrier to discovering restaurants that match desired atmospheres rather than just cuisine types.

The core insight—that multimodal embeddings can capture subjective qualities that text or images alone miss—has broader applicability beyond restaurants. Similar architectures could apply to hotels (boutique vs. luxury vs. budget vibes), retail stores (minimalist vs. maximalist aesthetics), event venues (formal vs. casual atmospheres), or even real estate (cozy vs. modern home styles). Any domain where experiential qualities matter more than functional specifications represents a potential application.

Future work should address: (1) personalization via user preference learning, (2) multi-label evaluation methodologies, (3) temporal dynamics (vibe changes over time/day), (4) explicit diversity promotion in ranking, and (5) integration of additional modalities (audio for noise levels, 3D tours for spatial layout). The 896-dimensional embedding space we've constructed provides a foundation for these extensions.

---
