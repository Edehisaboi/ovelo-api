from typing import List
import logging
from api.services.tmdb import TranscriptChunk
from config import Settings, get_openai_client
from .client import EmbeddingClient

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for handling text embeddings and transcript processing."""

    def __init__(self, client: EmbeddingClient = None):
        self.client = client or EmbeddingClient(
            client=get_openai_client()
        )

    async def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        try:
            return await self.client.create_embedding(text)
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            raise

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        try:
            return await self.client.create_embeddings(texts)
        except Exception as e:
            logger.error(f"Error getting embeddings: {str(e)}")
            raise

    async def update_with_embeddings(self, transcript_chunks: List[TranscriptChunk]) -> List[TranscriptChunk]:
        """Generate embeddings for each transcript chunk and update them with the corresponding embedding."""
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
