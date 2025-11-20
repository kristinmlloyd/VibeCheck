"""Streamlit web application for VibeCheck."""

import os

import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image

from vibecheck import VibeCheckRecommender

st.set_page_config(page_title="VibeCheck", layout="wide")


# Initialize recommender (cached)
@st.cache_resource
def load_recommender():
    """Load the VibeCheck recommender system."""
    return VibeCheckRecommender()


recommender = load_recommender()
VIBE_MAP_CSV = "data/processed/vibe_map.csv"

# UI code - same as before but using recommender API
st.title("🍽️ VibeCheck — Restaurant Vibe Discovery")

st.markdown(
    """
Find restaurants with a similar **atmosphere** — by photo or description.
Upload an image of a space you like, or describe your desired vibe in words.
"""
)

col_left, col_right = st.columns([2, 1])

with col_left:
    col_left1, col_right1 = st.columns([1, 1])

    with col_left1:
        query_text = st.text_input(
            "Describe your desired vibe:",
            placeholder="e.g., cozy cafe with plants and warm lighting",
        )
        query_image = st.file_uploader("Or upload an image", type=["jpg", "png"])

    with col_right1:
        if query_image:
            img = Image.open(query_image).resize((200, 200))
            st.image(img, caption="Your uploaded image")
        else:
            st.markdown("<div style='height:250px'></div>", unsafe_allow_html=True)

    if st.button("🔍 Search"):
        if not query_text and not query_image:
            st.warning("Please enter text or upload an image to search!")
        else:
            # Use the recommender API
            if query_text and query_image:
                img = Image.open(query_image)
                results = recommender.search_multimodal(
                    text=query_text, image=img, top_k=6
                )
            elif query_text:
                results = recommender.search_by_text(query_text, top_k=6)
            else:
                img = Image.open(query_image)
                results = recommender.search_by_image(img, top_k=6)

            st.subheader("Top Vibe Matches")

            # Display results in grid
            cols_per_row = 3
            for i in range(0, len(results), cols_per_row):
                row_results = results[i : i + cols_per_row]
                cols = st.columns(len(row_results))

                for col, resto in zip(cols, row_results, strict=False):
                    with col:
                        if resto["image_path"] and os.path.exists(resto["image_path"]):
                            img = Image.open(resto["image_path"]).resize((200, 200))
                            st.image(img)
                        st.markdown(
                            f"**{resto['name']}** — ⭐ {resto['rating']}\n\n📍 {resto['address']}"
                        )

with col_right:
    st.header("🎨 Explore the Restaurant Vibe Map")

    VIBE_MAP_CSV = "data/processed/vibe_map.csv"
    if os.path.exists(VIBE_MAP_CSV):
        try:
            df_map = pd.read_csv(VIBE_MAP_CSV)
            df_map["cluster"] = df_map["cluster"].astype(str)

            fig = px.scatter(
                df_map,
                x="x",
                y="y",
                color="cluster",
                hover_data=["name", "rating", "categories"],
                title="Aesthetic Map of Restaurant Vibes (UMAP + HDBSCAN)",
                width=600,
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Error loading/displaying map: {str(e)}")
    else:
        st.warning("Run `python vibecheck_map.py` first to generate the aesthetic map.")
