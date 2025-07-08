from typing import List, Dict

from external.clients import EmbeddingClient
from application.models.media import TranscriptChunk
from application.core.logging import get_logger
from external.clients import embedding_client

logger = get_logger(__name__)


class EmbeddingService:
    """Service for handling text embeddings and transcript processing."""

    def __init__(self, client: EmbeddingClient = None):
        self.client = client or embedding_client

    async def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        try:
            embedding = await self.client.create_embedding(text)
            return embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            raise

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []

        try:
            embeddings = await self.client.create_embeddings(texts)
            return embeddings
        except Exception as e:
            logger.error(f"Error getting embeddings: {str(e)}")
            raise

    async def update_with_embeddings(
        self,
        transcript_chunks: List[TranscriptChunk]
    ) -> List[TranscriptChunk]:
        """Generate embeddings for each transcript chunk and update them."""
        if not transcript_chunks:
            logger.warning("No transcript chunks to update with embeddings")
            return []

        try:
            texts = [tc.text for tc in transcript_chunks]
            embeddings = await self.get_embeddings(texts)
            
            return [
                transcript_chunk.model_copy(update={"embedding": embedding})
                for transcript_chunk, embedding in zip(transcript_chunks, embeddings)
            ]
        except Exception as e:
            logger.error(f"Error updating transcript chunks with embeddings: {str(e)}")
            raise


# Create singleton instance
embedding_service = EmbeddingService()

__all__ = [
    "embedding_service",
    "EmbeddingService"
]

"""
Embedding service module for handling vector embeddings.
This module provides high-level functionality for working with embeddings,
while the actual client implementation is in the external/clients directory.
""" 