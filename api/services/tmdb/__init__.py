from .client import TMDbClient
from .search import search_media
from .models import TranscriptChunk
from config import Settings, get_http_client

# Create singleton instance
tmdb_client = TMDbClient(
    api_key=Settings.TMDB_API_KEY,
    http_client=get_http_client(),
    base_url=Settings.TMDB_BASE_URL
)

__all__ = ["tmdb_client", "search_media", "TranscriptChunk"]
