"""
VibeCheck Gradio Application for Hugging Face Spaces
====================================================
Main application entry point for Hugging Face Spaces deployment.
"""

import os
import sqlite3
from pathlib import Path
from typing import List, Optional, Tuple

import clip
import faiss
import gradio as gr
import numpy as np
import torch
from PIL import Image
from sentence_transformers import SentenceTransformer

# ==============================================================================
# CONFIG
# ==============================================================================

DATA_DIR = Path("./data")
DB_PATH = DATA_DIR / "vibecheck.db"
IMAGE_DIR = DATA_DIR / "images"
FAISS_PATH = DATA_DIR / "vibecheck_index.faiss"
META_PATH = DATA_DIR / "meta_ids.npy"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ==============================================================================
# LOAD MODELS
# ==============================================================================

print("Loading models...")
text_model = SentenceTransformer("all-MiniLM-L6-v2", device=DEVICE)
clip_model, clip_preprocess = clip.load("ViT-B/32", device=DEVICE)
faiss_index = faiss.read_index(str(FAISS_PATH))
meta_ids = np.load(META_PATH)
print(f"✅ Models loaded. FAISS index has {len(meta_ids)} restaurants.")

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def encode_query(text: Optional[str] = None, image: Optional[Image.Image] = None):
    """Encode text and/or image query into combined embedding."""
    # Text embedding
    text_vec = text_model.encode(
        text or "", convert_to_numpy=True, normalize_embeddings=True
    )

    # Image embedding
    if image is not None:
        try:
            img = image.convert("RGB")
            img_tensor = clip_preprocess(img).unsqueeze(0).to(DEVICE)
            with torch.no_grad():
                img_vec = clip_model.encode_image(img_tensor)
            img_vec /= img_vec.norm(dim=-1, keepdim=True)
            img_vec = img_vec.cpu().numpy()[0]
        except Exception as e:
            print(f"Error processing image: {e}")
            img_vec = np.zeros((512,))
    else:
        img_vec = np.zeros((512,))

    # Combine embeddings
    combined = np.concatenate([text_vec, img_vec]).astype("float32")
    return combined[None, :]


def get_restaurant_details(restaurant_id: int) -> Optional[dict]:
    """Get full restaurant details from database."""
    conn = get_db()
    cursor = conn.cursor()

    # Get basic info
    cursor.execute(
        """
        SELECT id, name, rating, address, reviews_count, place_id
        FROM restaurants
        WHERE id = ?
    """,
        (restaurant_id,),
    )

    row = cursor.fetchone()
    if not row:
        return None

    restaurant = dict(row)

    # Get photos
    cursor.execute(
        """
        SELECT local_filename, photo_url
        FROM vibe_photos
        WHERE restaurant_id = ?
        LIMIT 1
    """,
        (restaurant_id,),
    )

    photo = cursor.fetchone()
    restaurant["photo_filename"] = photo["local_filename"] if photo else None

    # Get vibes
    cursor.execute(
        """
        SELECT vibe_name, mention_count
        FROM vibe_analysis
        WHERE restaurant_id = ?
        ORDER BY mention_count DESC
        LIMIT 3
    """,
        (restaurant_id,),
    )

    vibes = cursor.fetchall()
    restaurant["vibes"] = [
        {"name": v["vibe_name"], "count": v["mention_count"]} for v in vibes
    ]

    # Get sample reviews
    cursor.execute(
        """
        SELECT review_text, likes
        FROM reviews
        WHERE restaurant_id = ?
        ORDER BY likes DESC
        LIMIT 2
    """,
        (restaurant_id,),
    )

    reviews = cursor.fetchall()
    restaurant["reviews"] = [
        {"text": r["review_text"][:150] + "...", "likes": r["likes"]} for r in reviews
    ]

    conn.close()
    return restaurant


def format_restaurant_result(restaurant: dict, image_path: Optional[Path]) -> str:
    """Format restaurant details as HTML."""
    vibes_str = ", ".join([v["name"] for v in restaurant["vibes"]]) if restaurant["vibes"] else "N/A"

    reviews_html = ""
    if restaurant["reviews"]:
        reviews_html = "<br>".join([
            f"• {r['text']} (👍 {r['likes']})" for r in restaurant["reviews"]
        ])

    html = f"""
    <div style="border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 8px;">
        <h3>{restaurant['name']}</h3>
        <p><strong>Rating:</strong> {'⭐' * int(float(restaurant['rating'] or 0))} {restaurant['rating']}/5.0</p>
        <p><strong>Address:</strong> {restaurant['address']}</p>
        <p><strong>Reviews:</strong> {restaurant['reviews_count']}</p>
        <p><strong>Top Vibes:</strong> {vibes_str}</p>
        <p><strong>Sample Reviews:</strong></p>
        <div style="margin-left: 20px; font-size: 0.9em; color: #555;">
            {reviews_html}
        </div>
    </div>
    """
    return html


def search_restaurants(
    query_text: str, query_image: Optional[Image.Image], top_k: int = 6
) -> Tuple[str, List[Image.Image]]:
    """Search for restaurants based on text and/or image query."""
    try:
        if not query_text and query_image is None:
            return "❌ Please provide either text query or image (or both)!", []

        # Encode query
        query_vec = encode_query(query_text, query_image)

        # Search FAISS index
        distances, indices = faiss_index.search(query_vec, top_k)

        # Get restaurant details
        results_html = f"<h2>Top {top_k} Results</h2>"
        result_images = []

        for idx, distance in zip(indices[0], distances[0]):
            restaurant_id = int(meta_ids[idx])
            details = get_restaurant_details(restaurant_id)

            if details:
                # Load image
                image_path = None
                if details["photo_filename"]:
                    image_path = IMAGE_DIR / details["photo_filename"]
                    if image_path.exists():
                        result_images.append(Image.open(image_path))
                    else:
                        # Placeholder if image not found
                        result_images.append(None)

                # Format result
                results_html += format_restaurant_result(details, image_path)

        if not result_images:
            return "❌ No results found.", []

        return results_html, result_images

    except Exception as e:
        return f"❌ Error: {str(e)}", []


# ==============================================================================
# GRADIO INTERFACE
# ==============================================================================


def create_interface():
    """Create the Gradio interface."""

    with gr.Blocks(theme=gr.themes.Soft(), title="VibeCheck Restaurant Discovery") as demo:
        gr.Markdown(
            """
            # 🍽️ VibeCheck: Restaurant Discovery by Ambience

            Find restaurants based on their **vibe and atmosphere** using AI-powered multimodal search!

            - 📝 **Text Search**: Describe the ambience you're looking for (e.g., "cozy romantic lighting with rustic decor")
            - 🖼️ **Image Search**: Upload a photo of a restaurant atmosphere you like
            - 🔄 **Hybrid Search**: Combine both text and image for more precise results

            ---
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Search Input")
                text_input = gr.Textbox(
                    label="Describe the Vibe",
                    placeholder="E.g., 'warm cozy cafe with vintage furniture and soft lighting'",
                    lines=3
                )
                image_input = gr.Image(
                    label="Upload Reference Image (Optional)",
                    type="pil"
                )
                top_k_slider = gr.Slider(
                    minimum=3,
                    maximum=12,
                    value=6,
                    step=1,
                    label="Number of Results"
                )
                search_btn = gr.Button("🔍 Search Restaurants", variant="primary")

                gr.Markdown(
                    """
                    ### Tips for Better Results:
                    - Be specific about lighting, materials, and atmosphere
                    - Use descriptive adjectives (cozy, bright, industrial, etc.)
                    - Upload clear interior photos for image search
                    """
                )

            with gr.Column(scale=2):
                gr.Markdown("### Search Results")
                results_html = gr.HTML()
                results_gallery = gr.Gallery(
                    label="Restaurant Images",
                    columns=3,
                    height="auto"
                )

        # Connect search function
        search_btn.click(
            fn=search_restaurants,
            inputs=[text_input, image_input, top_k_slider],
            outputs=[results_html, results_gallery]
        )

        gr.Markdown(
            """
            ---
            ### About VibeCheck

            VibeCheck uses cutting-edge AI models (CLIP, Sentence-BERT, FAISS) to understand and match restaurant atmospheres.
            The system analyzes images and descriptions to find venues that match your desired vibe.

            **Technology Stack:** OpenAI CLIP • Sentence-BERT • FAISS • Gradio
            """
        )

    return demo


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    # Check if data files exist
    if not DB_PATH.exists():
        print(f"❌ Error: Database not found at {DB_PATH}")
        print("Please upload the required data files to the 'data/' directory.")
        exit(1)

    if not FAISS_PATH.exists():
        print(f"❌ Error: FAISS index not found at {FAISS_PATH}")
        print("Please upload the required data files to the 'data/' directory.")
        exit(1)

    print("\n" + "=" * 60)
    print("🍽️  VIBECHECK GRADIO APP STARTING")
    print("=" * 60)
    print(f"📊 Loaded {len(meta_ids)} restaurants")
    print(f"🌐 Launching Gradio interface...")
    print("=" * 60 + "\n")

    # Create and launch interface
    demo = create_interface()
    demo.launch()
