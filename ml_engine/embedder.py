"""Optional dense sentence embeddings (Sentence-BERT). Falls back silently to TF-IDF only."""
import hashlib
import os
from pathlib import Path

import numpy as np

CACHE = Path(__file__).resolve().parents[1] / "data" / "cache"
DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class Embedder:
    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer  # optional dependency

        self.name = model_name
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> np.ndarray:
        return np.asarray(self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False))

    def encode_cached(self, texts: list[str]) -> np.ndarray:
        key = hashlib.sha1(("\n".join(texts) + self.name).encode()).hexdigest()[:16]
        path = CACHE / f"emb_{key}.npy"
        if path.exists():
            return np.load(path)
        emb = self.encode(texts)
        CACHE.mkdir(parents=True, exist_ok=True)
        np.save(path, emb)
        return emb


def load_embedder():
    """Return an Embedder, or None when sentence-transformers or the model is unavailable."""
    if os.getenv("PIRS_USE_DENSE", "1") == "0":
        return None
    try:
        return Embedder(os.getenv("PIRS_EMBED_MODEL", DEFAULT_MODEL))
    except Exception:
        return None
