from typing import List, Optional

from application.models import TranscriptChunk
from application.core.logging import get_logger
from application.core.dependencies import embedding_client

from external.clients.openai import EmbeddingClient

logger = get_logger(__name__)


class EmbeddingService:
    """Service for handling text embeddings and transcript processing."""

    def __init__(self, client: Optional[EmbeddingClient] = None):
        if client is None:
            client = embedding_client()
        self.client = client

    async def update_with_embeddings(
        self,
        transcript_chunks: List[TranscriptChunk]
    ) -> List[TranscriptChunk]:
        """Generate embeddings for each transcript chunk and update them."""
        if not transcript_chunks:
            logger.warning("No transcript chunks to update with embeddings")
            return []

        try:
            texts = [tc.text.lower() for tc in transcript_chunks]
            embeddings = await self.client.embedding.aembed_documents(texts)
            
            return [
                transcript_chunk.model_copy(update={"embedding": embedding})
                for transcript_chunk, embedding in zip(transcript_chunks, embeddings)
            ]
        except Exception as e:
            logger.error(f"Error updating transcript chunks with embeddings: {str(e)}")
            raise
