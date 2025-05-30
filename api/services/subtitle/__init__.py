from api.clients import OpenSubtitlesClient
from .chunker import SubtitleProcessor
from config import get_opensubtitles_client

# Create singleton instance
opensubtitles_client = get_opensubtitles_client()
subtitle_processor = SubtitleProcessor()

__all__ = [
    # Instances
    "opensubtitles_client",
    "subtitle_processor",
    # Classes Models
    "OpenSubtitlesClient",
    "SubtitleProcessor"
]
