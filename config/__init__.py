from .settings import Settings
from .logging import get_logger
from .dependencies import (
    get_settings,
    get_http_client,
    get_movie_db,
    get_tv_db,
    get_embedding_client,
    get_tmdb_client,
    get_opensubtitles_client,
    get_tmdb_rate_limiter,
    get_opensubtitles_rate_limiter,
    # FastAPI dependencies
)
from dotenv import load_dotenv

load_dotenv()

# Create singleton instances
settings = get_settings()
http_client = get_http_client()
movie_db = get_movie_db()
tv_db = get_tv_db()
embedding_client = get_embedding_client()
tmdb_client = get_tmdb_client()
opensubtitles_client = get_opensubtitles_client()
tmdb_rate_limiter = get_tmdb_rate_limiter()
opensubtitles_rate_limiter = get_opensubtitles_rate_limiter()

__all__ = [
    # Settings
    'settings',
    'Settings',

    # Core instances
    'http_client',
    'movie_db',
    'tv_db',
    'embedding_client',

    # API clients
    'tmdb_client',
    'opensubtitles_client',

    # Rate limiters
    'tmdb_rate_limiter',
    'opensubtitles_rate_limiter',

    # FastAPI dependencies

    # Logging
    'get_logger'
]
