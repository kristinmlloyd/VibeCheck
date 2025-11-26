"""ML Service for model inference."""

import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="VibeCheck ML Service",
    description="Model inference service",
    version="0.1.0",
)

_models = {}


class TextEmbeddingRequest(BaseModel):
    text: str


class EmbeddingResponse(BaseModel):
    embedding: list[float]
    dimensions: int


class HealthResponse(BaseModel):
    status: str
    service: str
    models_loaded: list[str]


def get_text_model():
    if "text" not in _models:
        logger.info("Loading text model...")
        from sentence_transformers import SentenceTransformer

        _models["text"] = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        logger.info("Text model loaded")
    return _models["text"]


def get_clip_model():
    if "clip" not in _models:
        logger.info("Loading CLIP model...")
        import clip
        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        model, preprocess = clip.load("ViT-B/32", device=device)
        _models["clip"] = model
        _models["clip_preprocess"] = preprocess
        _models["device"] = device
        logger.info("CLIP model loaded")
    return _models["clip"], _models["clip_preprocess"], _models["device"]


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        service="vibecheck-ml",
        models_loaded=list(_models.keys()),
    )


@app.post("/embed/text", response_model=EmbeddingResponse)
async def embed_text(request: TextEmbeddingRequest):
    try:
        model = get_text_model()
        embedding = model.encode(
            request.text, convert_to_numpy=True, normalize_embeddings=True
        )
        return EmbeddingResponse(
            embedding=embedding.tolist(), dimensions=len(embedding)
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.on_event("startup")
async def startup_event():
    logger.info("Pre-loading models...")
    try:
        get_text_model()
        get_clip_model()
        logger.info("Models loaded successfully")
    except Exception as e:
        logger.error(f"Error loading models: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
