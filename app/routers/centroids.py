from fastapi import APIRouter, HTTPException, Query
from ..db import get_conn, api_upsert_dog_part_centroid
import numpy as np

router = APIRouter(prefix="/v1", tags=["centroids"])

@router.post("/centroids/refresh-dog")
async def refresh_dog_centroids(dog_id: str = Query(...)):
    sql = """
    select
      pp.part,
      pp.embedding
    from public.photo_patches pp
    join public.photos p on p.id = pp.photo_id
    where p.dog_id = %s
    """
    parts = {}
    async with get_conn() as (_, cur):
        await cur.execute(sql, (dog_id,))
        rows = await cur.fetchall()

    for r in rows:
        part = r["part"] or "unknown"
        vec = np.array(r["embedding"], dtype=np.float32)
        parts.setdefault(part, []).append(vec)

    if not parts:
        raise HTTPException(404, "No patches found for this dog")

    for part, vecs in parts.items():
        V = np.stack(vecs, axis=0)
        mean = V.mean(axis=0)
        norm = np.linalg.norm(mean) + 1e-9
        centroid = (mean / norm).astype("float32").tolist()
        await api_upsert_dog_part_centroid(dog_id, part, centroid, len(vecs))

    return {"dog_id": dog_id, "parts_updated": list(parts.keys())}
