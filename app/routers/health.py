from fastapi import APIRouter
router = APIRouter(prefix="/v1", tags=["health"])

@router.get("/health")
async def health():
    return {"ok": True}
