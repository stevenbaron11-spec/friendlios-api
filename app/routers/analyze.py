from typing import Optional
import httpx
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from PIL import Image
import numpy as np
import io

from ..db import api_upsert_photo_analysis, api_insert_photo_patch
from ..services.markings import phash64, lab_histogram, lbp_histogram, pick_distinctive_patches

router = APIRouter(prefix="/v1", tags=["analyze"])

async def _load_image(file: UploadFile | None, url: Optional[str]) -> Image.Image:
    if file is not None:
        data = await file.read()
        if not data:
            raise HTTPException(400, "Empty file")
        return Image.open(io.BytesIO(data)).convert("RGB")
    if url:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url)
            r.raise_for_status()
            return Image.open(io.BytesIO(r.content)).convert("RGB")
    raise HTTPException(400, "Provide file or url")

def _rand_vec(dim: int = 128) -> list[float]:
    v = np.random.rand(dim).astype("float32")
    v /= (np.linalg.norm(v) + 1e-9)
    return v.tolist()

@router.post("/analyze")
async def analyze(
    photo_id: str = Query(..., description="Existing public.photos.id"),
    file: UploadFile | None = File(None),
    url: Optional[str] = Query(None)
):
    img = await _load_image(file, url)
    phash = phash64(img)
    lab  = lab_histogram(img, bins=16)
    gray = np.asarray(img.convert("L"), dtype=np.float32)
    lbp  = lbp_histogram(gray)

    patches = pick_distinctive_patches(img, k=5, win=64, stride=32)
    await api_upsert_photo_analysis(photo_id, phash, lab, lbp, attributes_json={})
    for (x, y, w, h, score) in patches:
        vec = _rand_vec(128)
        await api_insert_photo_patch(photo_id=photo_id, part="unknown", bbox=[x, y, w, h], embedding_vec=vec, score=float(score))

    return {"photo_id": photo_id, "patches_saved": len(patches)}
