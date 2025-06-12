from .opensubtitles import OpenSubtitlesClient
from .tmdb import TMDbClient
from .openai import EmbeddingClient

embedding_client = EmbeddingClient()

__all__ = [
    # Classes
    "OpenSubtitlesClient",
    "TMDbClient",
    "EmbeddingClient",
    # Instances
    "embedding_client"
]