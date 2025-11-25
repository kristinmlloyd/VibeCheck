"""Streamlit web application for VibeCheck restaurant recommendations."""

import logging
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image

from vibecheck import VibeCheckRecommender, setup_logging

# Configure logging
setup_logging(level=logging.INFO)
logger = logging.getLogger("vibecheck.app")

st.set_page_config(page_title="VibeCheck", layout="wide")

# Configuration
VIBE_MAP_CSV = "data/processed/vibe_map.csv"

logger.info("Starting VibeCheck Streamlit application")


@st.cache_resource
def load_recommender():
    """Load the VibeCheck recommender system."""
    logger.info("Loading recommender (cached)")
    return VibeCheckRecommender()


recommender = load_recommender()

# UI
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
            logger.warning("Search attempted with no input")
            st.warning("Please enter text or upload an image to search!")
        else:
            logger.info(
                f"Search initiated - text: {bool(query_text)}, image: {bool(query_image)}"
            )

            try:
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

                logger.info(f"Search returned {len(results)} results")

                st.subheader("Top Vibe Matches")

                # Display results in grid
                cols_per_row = 3
                for i in range(0, len(results), cols_per_row):
                    row_results = results[i : i + cols_per_row]
                    cols = st.columns(len(row_results))

                    for col, resto in zip(cols, row_results, strict=False):
                        with col:
                            img_path = (
                                Path("data/images/sample_images") / f"{resto['id']}.jpg"
                            )
                            if img_path.exists():
                                img = Image.open(img_path).resize((200, 200))
                                st.image(img)
                            st.markdown(
                                f"**{resto['name']}** — ⭐ {resto['rating']}\n\n📍 {resto['address']}"
                            )

            except Exception as e:
                logger.error(f"Search error: {e}", exc_info=True)
                st.error(f"An error occurred: {e}")

with col_right:
    st.header("🎨 Explore the Restaurant Vibe Map")

    if os.path.exists(VIBE_MAP_CSV):
        try:
            logger.debug(f"Loading vibe map from: {VIBE_MAP_CSV}")
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
            logger.debug("Vibe map displayed successfully")

        except Exception as e:
            logger.error(f"Error loading vibe map: {e}", exc_info=True)
            st.error(f"Error loading/displaying map: {str(e)}")
    else:
        logger.warning(f"Vibe map CSV not found: {VIBE_MAP_CSV}")
        st.warning(
            "Run `python scripts/create_vibe_map.py` first to generate the aesthetic map."
        )

logger.info("Streamlit app initialized successfully")
