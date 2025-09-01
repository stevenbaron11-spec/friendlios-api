def test_analyze_with_url(client, monkeypatch):
    import io
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (64,64), color=(128, 80, 40)).save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    class Resp:
        def __init__(self, content): self.content = content
        def raise_for_status(self): return None
    class FakeAsyncClient:
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc, tb): return False
        async def get(self, url): return Resp(img_bytes)

    import httpx
    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout=30: FakeAsyncClient())

    r = client.post("/v1/analyze", params={"photo_id":"11111111-1111-1111-1111-111111111111","url":"https://example.com/a.jpg"})
    assert r.status_code == 200
    js = r.json()
    assert js["photo_id"]
    assert js["patches_saved"] >= 0
