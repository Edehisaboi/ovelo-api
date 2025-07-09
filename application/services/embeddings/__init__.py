from .embedding import EmbeddingService

# Create singleton instance
embedding_service = EmbeddingService()

__all__ = [
    "EmbeddingService",
    "embedding_service"
]

"""
Embedding service module for handling vector embeddings.
This module provides high-level functionality for working with embeddings,
while the actual client implementation is in the external/clients directory.
"""