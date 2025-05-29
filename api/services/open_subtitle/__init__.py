from .client import OpenSubtitlesClient
from .chunker import SubtitleChunker
from config import Settings, get_http_client

# Create singleton instance
opensubtitles_client = OpenSubtitlesClient(
    api_key=Settings.OPENSUBTITLES_API_KEY,
    http_client=get_http_client(),
    base_url=Settings.OPENSUBTITLES_BASE_URL,
)

subtitle_chunker = SubtitleChunker()

__all__ = [
    # Instances
    "opensubtitles_client", "subtitle_chunker",
    # Classes Models
    "OpenSubtitlesClient", "SubtitleChunker"
]
