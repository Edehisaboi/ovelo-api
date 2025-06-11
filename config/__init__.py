from .settings import Settings
from .logging import get_logger
from .dependencies import (
    get_settings,
    get_http_client,
    get_mongo_client,
    get_mongo_db,
    get_movies_collection,
    get_tv_collection,
    get_openai_client,
    get_embedding_client,
    get_tmdb_client,
    get_opensubtitles_client,
    get_tmdb_rate_limiter,
    get_opensubtitles_rate_limiter,
    # FastAPI dependencies
)
from dotenv import load_dotenv

load_dotenv()

# Create a singleton instance
settings = get_settings()

__all__ = [
    # Settings
    'settings',
    'Settings',
    # Core dependencies
    'get_settings',
    'get_http_client',
    'get_mongo_client',
    'get_mongo_db',
    'get_movies_collection',
    'get_tv_collection',
    # API clients
    'get_openai_client',
    'get_embedding_client',
    'get_tmdb_client',
    'get_opensubtitles_client',
    # Rate limiters
    'get_tmdb_rate_limiter',
    'get_opensubtitles_rate_limiter',
    # FastAPI dependencies
    # Logging
    'get_logger'
]
