from api.clients import TMDbClient
from .search import search_media, search_movies, search_tv_shows
from .model import TranscriptChunk
from config import get_tmdb_client

# Create singleton instance
tmdb_client = get_tmdb_client()

__all__ = [
    # Instances
    "tmdb_client",
    # Classes Models
    "TMDbClient", "TranscriptChunk",
    # Methods
    "search_media", "search_movies", "search_tv_shows"
]
