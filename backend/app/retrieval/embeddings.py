import numpy as np

from app.log_config.logger import get_logger


class EmbeddingService:
    _cache: dict[str, list[float]] = {}

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self.logger = get_logger(self.__class__.__name__)

    def _load_model(self):
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            self.logger.info(f"Loaded embedding model: {self.model_name}")
        except ImportError:
            self.logger.warning("sentence-transformers not available, using fallback embeddings")
            self._model = None
        except Exception as e:
            self.logger.warning(f"Failed to load embedding model: {e}, using fallback")
            self._model = None

    async def embed(self, text: str) -> list[float]:
        if text in self._cache:
            return self._cache[text]

        self._load_model()
        emb_list = []
        if self._model is not None:
            try:
                emb = self._model.encode(text, normalize_embeddings=True)
                emb_list = emb.tolist()
            except Exception as e:
                self.logger.warning(f"Embedding failed: {e}, using fallback")
                emb_list = self._fallback_embed(text)
        else:
            emb_list = self._fallback_embed(text)
        
        self._cache[text] = emb_list
        return emb_list

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        results = []
        to_compute = []
        to_compute_indices = []

        for i, text in enumerate(texts):
            if text in self._cache:
                results.append(self._cache[text])
            else:
                results.append(None) # Placeholder
                to_compute.append(text)
                to_compute_indices.append(i)

        if to_compute:
            self._load_model()
            computed_embs = []
            if self._model is not None:
                try:
                    embs = self._model.encode(to_compute, normalize_embeddings=True)
                    computed_embs = [e.tolist() for e in embs]
                except Exception as e:
                    self.logger.warning(f"Batch embedding failed: {e}, using fallback")
                    computed_embs = [self._fallback_embed(t) for t in to_compute]
            else:
                computed_embs = [self._fallback_embed(t) for t in to_compute]
            
            for i, emb in zip(to_compute_indices, computed_embs):
                results[i] = emb
                self._cache[texts[i]] = emb

        return results

    def _fallback_embed(self, text: str) -> list[float]:
        words = text.lower().split()
        vec = np.zeros(384)
        for w in words:
            h = hash(w) % 384
            vec[h] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def cosine_similarity(self, a: list[float], b: list[float]) -> float:
        arr_a = np.array(a)
        arr_b = np.array(b)
        dot = np.dot(arr_a, arr_b)
        norm = np.linalg.norm(arr_a) * np.linalg.norm(arr_b)
        return float(dot / norm) if norm > 0 else 0.0

    async def rank_by_similarity(self, query: str, candidates: list[dict], text_field: str = "snippet") -> list[dict]:
        query_emb = await self.embed(query)
        texts = [c.get(text_field, "") or "" for c in candidates]
        candidate_embs = await self.embed_batch(texts)
        scored = []
        for c, emb in zip(candidates, candidate_embs):
            sim = self.cosine_similarity(query_emb, emb)
            scored.append({**c, "_similarity": round(sim, 4)})
        scored.sort(key=lambda x: x["_similarity"], reverse=True)
        return scored
