from fastapi import APIRouter, UploadFile, File, HTTPException
import httpx
import uuid
from ..config import settings

router = APIRouter(prefix="/v1", tags=["photos"])

@router.post("/upload")
async def upload_photo(file: UploadFile = File(...)):
    data = await file.read()
    if len(data) == 0:
        raise HTTPException(400, "Empty file")
    object_name = f"{uuid.uuid4()}.jpg"
    url = f"{settings.supabase_url}/storage/v1/object/{settings.photos_bucket}/{object_name}"
    headers = {
        "Authorization": f"Bearer {settings.supabase_service_key}",
        "Content-Type": file.content_type or "image/jpeg",
        "x-upsert": "true",
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, headers=headers, content=data)
        r.raise_for_status()
    public_url = f"{settings.supabase_url}/storage/v1/object/public/{settings.photos_bucket}/{object_name}"
    return {"url": public_url}
