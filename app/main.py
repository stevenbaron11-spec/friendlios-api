from fastapi import FastAPI
from .db import init_db, close_db
from .services.embedding import init_embedder
from .routers import health, match, photos, analyze, centroids, dogs, notify, links

app = FastAPI(title="PetID API", version="1.2")

@app.on_event("startup")
async def _startup():
    await init_db()
    init_embedder()

@app.on_event("shutdown")
async def _shutdown():
    await close_db()

app.include_router(health.router)
app.include_router(match.router)
app.include_router(photos.router)
app.include_router(analyze.router)
app.include_router(centroids.router)
app.include_router(dogs.router)
app.include_router(notify.router)
app.include_router(links.router)
