from api.clients import OpenSubtitlesClient
from .chunker import SubtitleProcessor
from config import Settings, get_http_client
from ..rateLimiting.limiter import RateLimiter

# Create singleton instance
opensubtitles_client = OpenSubtitlesClient(
    api_key=Settings.OPENSUBTITLES_API_KEY,
    http_client=get_http_client(),
    base_url=Settings.OPENSUBTITLES_BASE_URL,
    rate_limiter=RateLimiter.from_settings(Settings(), "opensubtitles")
)

subtitle_processor = SubtitleProcessor()

__all__ = [
    # Instances
    "opensubtitles_client",
    "subtitle_processor",
    # Classes Models
    "OpenSubtitlesClient",
    "SubtitleProcessor"
]
