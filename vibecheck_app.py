import os
import sqlite3
import numpy as np
import torch
import clip
from PIL import Image
import streamlit as st
from sentence_transformers import SentenceTransformer
import faiss
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="VibeCheck", layout="wide")

DB_PATH = "restaurants.db"
IMAGE_DIR = "sample_images"
FAISS_PATH = "vibecheck_index.faiss"
META_PATH = "meta_ids.npy"
VIBE_MAP_CSV = "vibe_map.csv"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

@st.cache_resource
def load_models():
    text_model = SentenceTransformer("all-MiniLM-L6-v2", device=DEVICE)
    clip_model, clip_preprocess = clip.load("ViT-B/32", device=DEVICE)
    index = faiss.read_index(FAISS_PATH)
    meta_ids = np.load(META_PATH)
    return text_model, clip_model, clip_preprocess, index, meta_ids

text_model, clip_model, clip_preprocess, index, meta_ids = load_models()


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
            placeholder="e.g., cozy cafe with plants and warm lighting"
        )
        query_image = st.file_uploader("Or upload an image", type=["jpg", "png"])

    with col_right1:
        if query_image:
            img_size = (200, 200)  
            img = Image.open(query_image)
            img = img.resize(img_size)
            st.image(img, caption="Your uploaded image")
        else:
            st.empty()
            st.markdown("<div style='height:250px'></div>", unsafe_allow_html=True)


    # query_text = st.text_input("Describe your desired vibe:", placeholder="e.g., cozy cafe with plants and warm lighting")
    # query_image = st.file_uploader("Or upload an image", type=["jpg", "png"])
    
    # if query_image:
    #     img_size = (200, 200)
    #     img = Image.open(query_image)
    #     img = img.resize(img_size)
    #     st.image(img, caption="Your uploaded image")

    def encode_query(text=None, image=None):
        t_vec = text_model.encode(text or "", convert_to_numpy=True, normalize_embeddings=True)
        
        if image:
            img = clip_preprocess(Image.open(image)).unsqueeze(0).to(DEVICE)
            with torch.no_grad():
                i_vec = clip_model.encode_image(img)
            i_vec /= i_vec.norm(dim=-1, keepdim=True)
            i_vec = i_vec.cpu().numpy()[0]
        else:
            i_vec = np.zeros((512,))
        
        return np.concatenate([t_vec, i_vec]).astype("float32")[None, :]

    def get_restaurant_info(rid):
        with sqlite3.connect(DB_PATH) as conn:
            row = conn.execute(
                "SELECT name, rating, address, image_url FROM restaurants WHERE id=?", (rid,)
            ).fetchone()
        return row  # returns tuple: (name, rating, address, image_url)

    # if st.button("🔍 Search"):
    #     if not query_text and not query_image:
    #         st.warning("Please enter text or upload an image to search!")
    #     else:
    #         query_vec = encode_query(query_text, query_image)
    #         D, I = index.search(query_vec, 5)
    #         results = [meta_ids[i] for i in I[0]]

    #         st.subheader("Top Vibe Matches")
    #         for rid in results:
    #             info = get_restaurant_info(rid)
    #             if not info:
    #                 continue
    #             name, rating, addr, img_url = info
    #             img_path = os.path.join(IMAGE_DIR, f"{rid}.jpg")
    #             if os.path.exists(img_path):
    #                 st.image(img_path, width=250)
    #             st.markdown(f"**{name}** — ⭐ {rating}\n\n📍 {addr}")



    if st.button("🔍 Search"):
        if not query_text and not query_image:
            st.warning("Please enter text or upload an image to search!")
        else:
            query_vec = encode_query(query_text, query_image)
            D, I = index.search(query_vec, 6)
            results = [meta_ids[i] for i in I[0]]

            st.subheader("Top Vibe Matches")

            cols_per_row = 3
            img_size = (200, 200)  # fixed width & height

            for i in range(0, len(results), cols_per_row):
                row_results = results[i:i+cols_per_row]
                cols = st.columns(len(row_results))
                for col, rid in zip(cols, row_results):
                    info = get_restaurant_info(rid)
                    if not info:
                        continue
                    name, rating, addr, img_url = info
                    img_path = os.path.join(IMAGE_DIR, f"{rid}.jpg")
                    with col:
                        if os.path.exists(img_path):
                            img = Image.open(img_path).resize(img_size)
                            st.image(img)
                        st.markdown(f"**{name}** — ⭐ {rating}\n\n📍 {addr}")



with col_right:
    st.header("🎨 Explore the Restaurant Vibe Map")
    if os.path.exists(VIBE_MAP_CSV):
        df_map = pd.read_csv(VIBE_MAP_CSV)
        df_map["cluster"] = df_map["cluster"].astype(str)
        fig = px.scatter(
            df_map,
            x="x",
            y="y",
            color="cluster",
            hover_data=["name", "rating", "categories"],
            title="Aesthetic Map of Restaurant Vibes (UMAP + HDBSCAN)",
            width=900,
            height=700
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Run `python vibecheck_map.py` first to generate the aesthetic map.")
