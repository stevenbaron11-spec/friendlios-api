from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="", tags=["links"])

@router.get("/l/dog/{dog_id}", response_class=HTMLResponse)
async def deep_link_dog(dog_id: str):
    # This is a simple fallback page; for production use a templated page and proper store links.
    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta property="og:title" content="See this dog on PetID">
  <meta property="og:description" content="Open in the PetID app to view details.">
  <meta property="og:url" content="https://petid.app/dog/{dog_id}">
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>PetID Link</title>
  <style>body{{font-family:sans-serif; padding:2rem;}}</style>
</head>
<body>
  <h1>Open in PetID</h1>
  <p>Dog ID: {dog_id}</p>
  <p><a href="https://petid.app/dog/{dog_id}">Continue</a></p>
  <p>If you have the app installed, this link will open it. Otherwise, it will open this page.</p>
</body>
</html>
"""
    return HTMLResponse(content=html)
