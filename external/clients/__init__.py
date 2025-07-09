from .opensubtitles import OpenSubtitlesClient
from .tmdb import TMDbClient

# Lazy-loaded embedding client to avoid circular imports
_embedding_client = None

def get_embedding_client():
    """Get a singleton instance of the embedding client."""
    global _embedding_client
    if _embedding_client is None:
        from .openai import EmbeddingClient
        _embedding_client = EmbeddingClient()
    return _embedding_client

__all__ = [
    # Classes
    "OpenSubtitlesClient",
    "TMDbClient", 
    # Functions
    "get_embedding_client"
] 