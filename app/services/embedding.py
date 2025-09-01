import os
import numpy as np
from ..config import settings

class BaseEmbedder:
    def embed(self, tensor: np.ndarray) -> list[float]:
        raise NotImplementedError

class RandomEmbedder(BaseEmbedder):
    def __init__(self, out_dim: int):
        self.out_dim = out_dim

    def embed(self, tensor: np.ndarray) -> list[float]:
        v = np.random.rand(self.out_dim).astype("float32")
        v /= (np.linalg.norm(v) + 1e-9)
        return v.tolist()

class OnnxEmbedder(BaseEmbedder):
    def __init__(self, model_path: str, out_dim: int):
        import onnxruntime as ort
        self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name
        self.out_dim = out_dim

    def embed(self, tensor: np.ndarray) -> list[float]:
        out = self.session.run(None, {self.input_name: tensor})[0]
        vec = out[0].astype("float32")
        vec /= (np.linalg.norm(vec) + 1e-9)
        return vec.tolist()

embedder: BaseEmbedder | None = None

def init_embedder():
    global embedder
    backend = settings.embedder_backend.lower().strip()
    if backend == "random":
        embedder = RandomEmbedder(settings.embed_vector_size)
        print("[embedder] Using RandomEmbedder")
    elif backend == "onnx":
        if not os.path.exists(settings.embed_model_path):
            raise FileNotFoundError(f"ONNX model not found at {settings.embed_model_path}")
        embedder = OnnxEmbedder(settings.embed_model_path, settings.embed_vector_size)
        print("[embedder] Using OnnxEmbedder:", settings.embed_model_path)
    else:
        raise ValueError(f"Unknown EMBEDDER_BACKEND: {backend}")
