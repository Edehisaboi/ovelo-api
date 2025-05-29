from .client import TMDbClient
from .search import search_media, search_movies, search_tv_shows
from .model import TranscriptChunk
from config import Settings, get_http_client

# Create singleton instance
tmdb_client = TMDbClient(
    api_key=Settings.TMDB_API_KEY,
    http_client=get_http_client(),
    base_url=Settings.TMDB_BASE_URL
)

__all__ = [
    # Instances
    "tmdb_client",
    # Classes Models
    "TMDbClient", "TranscriptChunk",
    # Methods
    "search_media", "search_movies", "search_tv_shows"
]
