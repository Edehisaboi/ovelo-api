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

    async def process_text(
            self,
            text: str
        ) -> TranscriptChunk:
        """Process a single text and return a TranscriptChunk."""
        embedding = await self.get_embedding(text)
        return TranscriptChunk(
            index=0,
            text=text,
            embedding=embedding
        )

    async def process_texts(
            self,
            texts: List[str]
        ) -> List[TranscriptChunk]:
        """Process multiple texts and return a list of TranscriptChunks."""
        embeddings = await self.get_embeddings(texts)
        return [
            TranscriptChunk(
                index=i,
                text=text,
                embedding=embedding
            )
            for i, (text, embedding) in enumerate(zip(texts, embeddings))
        ]


# Create singleton instance
embedding_service = EmbeddingService()


__all__ = [
    "embedding_service",
    "EmbeddingService"
]
