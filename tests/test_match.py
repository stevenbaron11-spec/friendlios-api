def test_match_with_url(client, monkeypatch):
    class Resp:
        def __init__(self, content=b"img"): self.content = content
        def raise_for_status(self): return None
    class FakeAsyncClient:
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc, tb): return False
        async def get(self, url): return Resp()

    import httpx
    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout=30: FakeAsyncClient())

    r = client.post("/v1/match", json={"photo_url":"https://example.com/dog.jpg","lat":12.34,"lon":56.78,"k":2})
    assert r.status_code == 200
    js = r.json()
    assert "candidates" in js and len(js["candidates"]) == 2

def test_confirm(client):
    r = client.post("/v1/confirm", params={"sighting_id":"s1", "chosen_dog_id":"d1"})
    assert r.status_code == 200
    assert r.json()["dog_id"] == "d1"
