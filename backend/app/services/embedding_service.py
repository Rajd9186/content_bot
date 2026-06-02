from __future__ import annotations

import logging
from typing import List, Optional
from app.core.config import settings
from app.agents.provider.factory import ProviderFactory

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Service for generating text embeddings using the configured LLM provider.
    """
    def __init__(self):
        self._provider_factory = ProviderFactory()

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Convert text to a 1536-dimension vector.
        """
        try:
            # We use the openai provider specifically for embeddings as it's the standard 1536
            provider = self._provider_factory.get_provider("openai")
            embedding = await provider.create_embedding(text)
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
