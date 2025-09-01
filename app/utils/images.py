from PIL import Image
import io
import numpy as np

def load_image_from_bytes(data: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(data)).convert("RGB")
    return img

def preprocess_for_embedding(img: Image.Image, size: int = 224) -> np.ndarray:
    img = img.resize((size, size))
    arr = np.asarray(img).astype("float32") / 255.0
    arr = (arr - 0.5) / 0.5
    arr = np.transpose(arr, (2, 0, 1))
    arr = np.expand_dims(arr, 0)
    return arr
