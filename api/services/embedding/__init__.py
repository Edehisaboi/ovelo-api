import logging
from typing import List, Dict, Optional
from functools import lru_cache
import time

from api.clients import EmbeddingClient
from api.services.tmdb import TranscriptChunk
from config import get_embedding_client, settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for handling text embeddings and transcript processing."""

    def __init__(self, client: EmbeddingClient = None):
        self.client = client or get_embedding_client()
        self._cache: Dict[str, List[float]] = {}
        self._cache_ttl = settings.EMBEDDING_CACHE_TTL
        self._max_cache_size = settings.EMBEDDING_CACHE_MAX_SIZE

    def _get_cache_key(self, text: str) -> str:
        """Generate a cache key for the given text."""
        return f"{text[:100]}"  # Use first 100 chars as key

    def _cleanup_cache(self) -> None:
        """Remove oldest entries if cache exceeds max size."""
        if len(self._cache) > self._max_cache_size:
            # Remove oldest entries
            sorted_items = sorted(
                self._cache.items(),
                key=lambda x: x[1][1],  # Sort by timestamp
                reverse=True
            )
            self._cache = dict(sorted_items[:self._max_cache_size])

    async def get_embedding(self, text: str, use_cache: bool = True) -> List[float]:
        """Generate embedding for a single text with optional caching."""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        if use_cache:
            cache_key = self._get_cache_key(text)
            if cache_key in self._cache:
                embedding, timestamp = self._cache[cache_key]
                if timestamp + self._cache_ttl > time.time():
                    return embedding

        try:
            embedding = await self.client.create_embedding(text)
            
            if use_cache:
                self._cleanup_cache()
                self._cache[cache_key] = (embedding, time.time())
            
            return embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            raise

    async def get_embeddings(self, texts: List[str], use_cache: bool = True) -> List[List[float]]:
        """Generate embeddings for multiple texts with optional caching."""
        if not texts:
            return []

        # Check cache first
        if use_cache:
            cached_embeddings = []
            texts_to_process = []
            
            for text in texts:
                cache_key = self._get_cache_key(text)
                if cache_key in self._cache:
                    embedding, timestamp = self._cache[cache_key]
                    if timestamp + self._cache_ttl > time.time():
                        cached_embeddings.append(embedding)
                        continue
                texts_to_process.append(text)
            
            if not texts_to_process:
                return cached_embeddings
        else:
            texts_to_process = texts
            cached_embeddings = []

        try:
            new_embeddings = await self.client.create_embeddings(texts_to_process)
            
            if use_cache:
                self._cleanup_cache()
                for text, embedding in zip(texts_to_process, new_embeddings):
                    cache_key = self._get_cache_key(text)
                    self._cache[cache_key] = (embedding, time.time())
            
            return cached_embeddings + new_embeddings
        except Exception as e:
            logger.error(f"Error getting embeddings: {str(e)}")
            raise

    async def update_with_embeddings(
        self,
        transcript_chunks: List[TranscriptChunk],
        use_cache: bool = True
    ) -> List[TranscriptChunk]:
        """Generate embeddings for each transcript chunk and update them."""
        if not transcript_chunks:
            logger.warning("No transcript chunks to update with embeddings")
            return []

        try:
            texts = [tc.text for tc in transcript_chunks]
            embeddings = await self.get_embeddings(texts, use_cache=use_cache)
            
            return [
                transcript_chunk.model_copy(update={"embedding": embedding})
                for transcript_chunk, embedding in zip(transcript_chunks, embeddings)
            ]
        except Exception as e:
            logger.error(f"Error updating transcript chunks with embeddings: {str(e)}")
            raise

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self._cache.clear()


# Create singleton instance
embedding_service = EmbeddingService()

__all__ = [
    "embedding_service",
    "EmbeddingService"
]

"""
Embedding service module for handling vector embeddings.
This module provides high-level functionality for working with embeddings,
while the actual client implementation is in the clients directory.
"""
