def test_refresh_centroids(client, monkeypatch):
    class FakeCur:
        async def execute(self, sql, params):
            self.rows = [
                {"part":"unknown", "embedding":[0.1,0.2,0.3]+[0.0]*125},
                {"part":"unknown", "embedding":[0.2,0.1,0.4]+[0.0]*125},
            ]
        async def fetchall(self): return self.rows
    class FakeCtx:
        async def __aenter__(self): return (None, FakeCur())
        async def __aexit__(self, exc_type, exc, tb): return False

    from app.routers import centroids as C
    monkeypatch.setattr(C, "get_conn", lambda: FakeCtx())

    r = client.post("/v1/centroids/refresh-dog", params={"dog_id":"11111111-1111-1111-1111-111111111111"})
    assert r.status_code == 200
    js = r.json()
    assert js["dog_id"]
    assert "parts_updated" in js
