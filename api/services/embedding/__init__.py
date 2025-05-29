from typing import List
from api.services.tmdb import TranscriptChunk
from config import Settings, get_openai_client
from .client import EmbeddingClient


class EmbeddingService:
    """Service for handling text embeddings and transcript processing."""
    def __init__(
            self,
            client: EmbeddingClient = None
        ):
        self.client = client or EmbeddingClient(
            client=get_openai_client(),
            model_name=Settings.OPENAI_EMBEDDING_MODEL
        )

    async def get_embedding(
            self,
            text: str
        ) -> List[float]:
        """Generate embedding for a single text."""
        return await self.client.create_embedding(text)

    async def get_embeddings(
            self,
            texts: List[str]
        ) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        return await self.client.create_embeddings(texts)

    async def update_with_embeddings(
            self,
            transcript_chunks: List[TranscriptChunk]
        ) -> List[TranscriptChunk]:
        """Generate embeddings for each transcript chunk and update them with the corresponding embedding."""
        return [
            transcript_chunk.model_copy(update={"embedding": embedding})
            for transcript_chunk, embedding in zip(
                transcript_chunks,
                await self.get_embeddings([tc.text for tc in transcript_chunks])
            )
        ]


# Create singleton instance
embedding_service = EmbeddingService()


__all__ = [
    # Instances
    "embedding_service",
    # Classes Models
    "EmbeddingService"
]
