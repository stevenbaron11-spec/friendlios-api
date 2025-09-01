import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.embedding import init_embedder
from app import db as dbmod

@pytest.fixture(autouse=True, scope="session")
def init_embedder_once():
    init_embedder()

@pytest.fixture(autouse=True)
def patch_db(monkeypatch):
    async def _noop_init_db(): return None
    async def _noop_close_db(): return None
    async def _noop_exec_sql(*args, **kwargs): return None
    async def _rpc_store_photo_embedding(photo_id, vec):
        patch_db.last_store = {"photo_id": photo_id, "dim": len(vec)}
    async def _rpc_match_dogs(vec, lat, lon, k=5):
        return [
            {"dog_id": "00000000-0000-0000-0000-000000000001", "display_name": "Buddy", "primary_photo_url": None,
             "visual": 0.9, "geo": 0.5, "recency": 0.8, "final_score": 0.88},
            {"dog_id": "00000000-0000-0000-0000-000000000002", "display_name": "Luna", "primary_photo_url": None,
             "visual": 0.85, "geo": 0.4, "recency": 0.7, "final_score": 0.82},
        ][:k]
    async def _rpc_confirm_match(sighting_id, chosen_dog_id, display_name):
        return chosen_dog_id or "11111111-1111-1111-1111-111111111111"
    async def _api_upsert_photo_analysis(photo_id, phash_bytes, lab_hist, lbp_hist, attributes_json): return None
    async def _api_insert_photo_patch(photo_id, part, bbox, embedding_vec, score): return None
    async def _api_upsert_dog_part_centroid(dog_id, part, centroid_vec, n_patches): return None

    monkeypatch.setattr(dbmod, "init_db", _noop_init_db)
    monkeypatch.setattr(dbmod, "close_db", _noop_close_db)
    monkeypatch.setattr(dbmod, "exec_sql", _noop_exec_sql)
    monkeypatch.setattr(dbmod, "rpc_store_photo_embedding", _rpc_store_photo_embedding)
    monkeypatch.setattr(dbmod, "rpc_match_dogs", _rpc_match_dogs)
    monkeypatch.setattr(dbmod, "rpc_confirm_match", _rpc_confirm_match)
    monkeypatch.setattr(dbmod, "api_upsert_photo_analysis", _api_upsert_photo_analysis)
    monkeypatch.setattr(dbmod, "api_insert_photo_patch", _api_insert_photo_patch)
    monkeypatch.setattr(dbmod, "api_upsert_dog_part_centroid", _api_upsert_dog_part_centroid)

@pytest.fixture()
def client():
    return TestClient(app)
