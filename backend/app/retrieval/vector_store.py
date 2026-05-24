from typing import Any
import numpy as np

from app.log_config.logger import get_logger
from app.retrieval.embeddings import EmbeddingService


class LocalVectorStore:
    def __init__(self, embedding_service: EmbeddingService):
        self.embeddings = embedding_service
        self._documents: list[dict] = []
        self._vectors: list[list[float]] = []
        self.logger = get_logger(self.__class__.__name__)

    async def add_document(self, doc: dict, text_field: str = "snippet") -> None:
        text = doc.get(text_field, "") or doc.get("content", "") or doc.get("claim_text", "") or ""
        if not text:
            return
        emb = await self.embeddings.embed(text)
        self._documents.append(doc)
        self._vectors.append(emb)

    async def add_documents(self, docs: list[dict], text_field: str = "snippet") -> None:
        for doc in docs:
            await self.add_document(doc, text_field)

    async def search(self, query: str, top_k: int = 5, min_score: float = 0.0) -> list[dict]:
        if not self._documents:
            return []
        query_emb = await self.embeddings.embed(query)
        vectors = np.array(self._vectors)
        scores = np.dot(vectors, query_emb)
        norms = np.linalg.norm(vectors, axis=1) * np.linalg.norm(query_emb)
        scores = np.divide(scores, norms, out=np.zeros_like(scores), where=norms > 0)
        
        # Apply Source Trust Weighting
        weighted_scores = []
        for idx, score in enumerate(scores):
            doc = self._documents[idx]
            # Trust score weighting (0.6 to 1.0)
            trust_weight = doc.get("score", 0.7) 
            # Weighted score: 70% semantic similarity + 30% trust
            final_score = (score * 0.7) + (trust_weight * 0.3)
            weighted_scores.append(final_score)
            
        top_indices = np.argsort(weighted_scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            score = float(weighted_scores[idx])
            if score < min_score:
                break
            results.append({**self._documents[idx], "_similarity": round(score, 4)})
        return results

    async def search_by_claim(self, claim_text: str, top_k: int = 3) -> list[dict]:
        return await self.search(claim_text, top_k=top_k, min_score=0.1)

    def clear(self) -> None:
        self._documents.clear()
        self._vectors.clear()

    @property
    def size(self) -> int:
        return len(self._documents)
