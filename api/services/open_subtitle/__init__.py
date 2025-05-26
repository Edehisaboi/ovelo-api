from .client import OpenSubtitlesClient
from config import Settings, get_http_client

# Create singleton instance
opensubtitles_client = OpenSubtitlesClient(
    api_key=Settings.OPENSUBTITLES_API_KEY,
    http_client=get_http_client(),
    base_url=Settings.OPENSUBTITLES_BASE_URL,
    settings=Settings()
)

__all__ = ["opensubtitles_client", "OpenSubtitlesClient"]
