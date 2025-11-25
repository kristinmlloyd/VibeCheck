"""FastAPI backend service for VibeCheck."""

import logging
import os
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="VibeCheck API",
    description="Restaurant recommendation API based on visual aesthetics",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TextSearchRequest(BaseModel):
    query: str
    top_k: int = 5


class RestaurantResult(BaseModel):
    id: str
    name: str
    rating: float | None
    address: str | None
    similarity: float


class SearchResponse(BaseModel):
    results: list[RestaurantResult]
    query_type: str


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


_recommender = None


def get_recommender():
    global _recommender
    if _recommender is None:
        logger.info("Initializing recommender...")
        from vibecheck import VibeCheckRecommender

        _recommender = VibeCheckRecommender(
            db_path=Path(os.getenv("DB_PATH", "data/restaurants_info/restaurants.db")),
            image_dir=Path(os.getenv("IMAGE_DIR", "data/images/sample_images")),
            faiss_index_path=Path(
                os.getenv("FAISS_INDEX_PATH", "data/embeddings/vibecheck_index.faiss")
            ),
            meta_ids_path=Path(
                os.getenv("META_IDS_PATH", "data/restaurants_info/meta_ids.npy")
            ),
        )
        logger.info("Recommender initialized")
    return _recommender


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", service="vibecheck-api", version="0.1.0")


@app.post("/api/search/text", response_model=SearchResponse)
async def search_by_text(request: TextSearchRequest):
    logger.info(f"Text search: '{request.query}'")
    try:
        recommender = get_recommender()
        results = recommender.search_by_text(request.query, top_k=request.top_k)
        return SearchResponse(
            results=[
                RestaurantResult(
                    id=r["id"],
                    name=r["name"],
                    rating=r.get("rating"),
                    address=r.get("address"),
                    similarity=r.get("similarity", 0.0),
                )
                for r in results
            ],
            query_type="text",
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/search/image", response_model=SearchResponse)
async def search_by_image(
    file: UploadFile = File(...),  # noqa: B008
    top_k: int = 5,
):
    logger.info("Image search")
    try:
        image = Image.open(file.file)
        recommender = get_recommender()
        results = recommender.search_by_image(image, top_k=top_k)
        return SearchResponse(
            results=[
                RestaurantResult(
                    id=r["id"],
                    name=r["name"],
                    rating=r.get("rating"),
                    address=r.get("address"),
                    similarity=r.get("similarity", 0.0),
                )
                for r in results
            ],
            query_type="image",
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/restaurants/{restaurant_id}")
async def get_restaurant(restaurant_id: str):
    try:
        recommender = get_recommender()
        info = recommender.get_restaurant_info(restaurant_id)
        if not info:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        return info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
