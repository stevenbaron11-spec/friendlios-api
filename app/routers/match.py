import base64
import httpx
from fastapi import APIRouter, UploadFile, File, HTTPException
from ..services.embedding import embedder
from ..utils.images import load_image_from_bytes, preprocess_for_embedding
from ..db import rpc_store_photo_embedding, rpc_match_dogs, rpc_confirm_match

router = APIRouter(prefix="/v1", tags=["match"])

@router.post("/embed")
async def embed_photo(photo_id: str, file: UploadFile = File(...)):
    if embedder is None:
        raise HTTPException(500, "Embedder not initialized")
    raw = await file.read()
    img = load_image_from_bytes(raw)
    tensor = preprocess_for_embedding(img)
    vec = embedder.embed(tensor)
    await rpc_store_photo_embedding(photo_id, vec)
    return {"photo_id": photo_id, "embedding_dim": len(vec)}

@router.post("/match")
async def match(photo_bytes_b64: str = None, photo_url: str = None, lat: float | None = None, lon: float | None = None, k: int = 5):
    if embedder is None:
        raise HTTPException(500, "Embedder not initialized")
    data = None
    if photo_bytes_b64:
        data = base64.b64decode(photo_bytes_b64)
    elif photo_url:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(photo_url)
            r.raise_for_status()
            data = r.content
    else:
        raise HTTPException(400, "Provide photo_bytes_b64 or photo_url")
    img = load_image_from_bytes(data)
    tensor = preprocess_for_embedding(img)
    vec = embedder.embed(tensor)
    rows = await rpc_match_dogs(vec, lat, lon, k)
    return {"candidates": rows}

@router.post("/confirm")
async def confirm(sighting_id: str, chosen_dog_id: str | None = None, display_name: str | None = None):
    dog_id = await rpc_confirm_match(sighting_id, chosen_dog_id, display_name)
    return {"dog_id": dog_id}
