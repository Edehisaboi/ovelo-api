from functools import lru_cache

import httpx

from config import settings, Settings
from api.services.database import movie_db, tv_db, MongoClientWrapper
from api.clients import (
    EmbeddingClient, OpenSubtitlesClient, TMDbClient,
    embedding_client
)
from api.services.rateLimiting.limiter import RateLimiter


@lru_cache()
def get_settings() -> Settings:
    """Get a singleton setting instance."""
    return Settings()


@lru_cache()
def get_http_client() -> httpx.AsyncClient:
    """Get a singleton HTTP client instance."""
    return httpx.AsyncClient()


@lru_cache()
def get_movie_db() -> MongoClientWrapper:
    """Get a singleton instance of the movie database wrapper."""
    return movie_db


@lru_cache()
def get_tv_db() -> MongoClientWrapper:
    """Get a singleton instance of the TV database wrapper."""
    return tv_db


@lru_cache()
def get_embedding_client() -> EmbeddingClient:
    """Get a singleton EmbeddingClient instance."""
    return embedding_client


@lru_cache()
def get_tmdb_client() -> TMDbClient:
    """Get a singleton TMDb client instance."""
    return TMDbClient(
        api_key        = settings.TMDB_API_KEY,
        http_client    = get_http_client(),
        rate_limiter   = get_tmdb_rate_limiter(),
        base_url       = settings.TMDB_BASE_URL
    )


@lru_cache()
def get_opensubtitles_client() -> OpenSubtitlesClient:
    """Get a singleton OpenSubtitles client instance."""
    return OpenSubtitlesClient(
        api_key        = settings.OPENSUBTITLES_API_KEY,
        http_client    = get_http_client(),
        rate_limiter   = get_opensubtitles_rate_limiter(),
        base_url       = settings.OPENSUBTITLES_BASE_URL
    )


@lru_cache()
def get_tmdb_rate_limiter() -> RateLimiter:
    """Get a singleton rate limiter for TMDb API."""
    return RateLimiter.from_settings("tmdb")


@lru_cache()
def get_opensubtitles_rate_limiter() -> RateLimiter:
    """Get a singleton rate limiter for OpenSubtitles API."""
    return RateLimiter.from_settings("opensubtitles")