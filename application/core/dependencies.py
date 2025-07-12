from functools import lru_cache
import httpx

from application.core.config import settings
from external.clients import (
    OpenSubtitlesClient,
    TMDbClient,
    EmbeddingClient,
    OpenAISTT,
    RekognitionClient,
)
from application.utils.rate_limiter import RateLimiter
from application.models import MovieDetails, TVDetails
from application.core.logging import get_logger
from infrastructure.database import MongoClientWrapper

logger = get_logger(__name__)


@lru_cache()
def get_embedding_client() -> EmbeddingClient:
    """Return a singleton EmbeddingClient instance."""
    return EmbeddingClient()

@lru_cache()
def get_movie_db() -> MongoClientWrapper:
    """Return a singleton movie database wrapper instance."""
    try:
        movie_db = MongoClientWrapper(
            model=MovieDetails,
            collection_name=settings.MOVIES_COLLECTION,
            database_name=settings.MONGODB_DB,
            mongodb_uri=settings.MONGODB_URL,
            embedding_client=get_embedding_client(),
        )
        movie_db.initialize_indexes()
        logger.info("Movie database connection initialized with indexes")
        return movie_db
    except Exception as e:
        logger.error(f"Failed to initialize movie database: {e}")
        raise

@lru_cache()
def get_tv_db() -> MongoClientWrapper:
    """Return a singleton TV database wrapper instance."""
    try:
        tv_db = MongoClientWrapper(
            model=TVDetails,
            collection_name=settings.TV_COLLECTION,
            database_name=settings.MONGODB_DB,
            mongodb_uri=settings.MONGODB_URL,
            embedding_client=get_embedding_client(),
        )
        tv_db.initialize_indexes()
        logger.info("TV database connection initialized with indexes")
        return tv_db
    except Exception as e:
        logger.error(f"Failed to initialize TV database: {e}")
        raise


@lru_cache()
def get_stt_client() -> OpenAISTT:
    """Return a singleton OpenAI STT client instance."""
    return OpenAISTT()


@lru_cache()
def get_tmdb_rate_limiter() -> RateLimiter:
    """Return a singleton rate limiter for TMDb API."""
    return RateLimiter.from_settings("tmdb")

@lru_cache()
def get_tmdb_client() -> TMDbClient:
    """Return a singleton TMDb client instance."""
    return TMDbClient(
        api_key=settings.TMDB_API_KEY,
        http_client=httpx.AsyncClient(),
        rate_limiter=get_tmdb_rate_limiter(),
        base_url=settings.TMDB_BASE_URL,
    )


@lru_cache()
def get_opensubtitles_rate_limiter() -> RateLimiter:
    """Return a singleton rate limiter for OpenSubtitles API."""
    return RateLimiter.from_settings("opensubtitles")

@lru_cache()
def get_opensubtitles_client() -> OpenSubtitlesClient:
    """Return a singleton OpenSubtitles client instance."""
    return OpenSubtitlesClient(
        api_key=settings.OPENSUBTITLES_API_KEY,
        http_client=httpx.AsyncClient(follow_redirects=True),
        rate_limiter=get_opensubtitles_rate_limiter(),
        base_url=settings.OPENSUBTITLES_BASE_URL,
    )


@lru_cache()
def get_rekognition_client() -> RekognitionClient:
    """Return a singleton Rekognition client instance."""
    return RekognitionClient()


def close_database_connections():
    """
    Close all open MongoDB connections (movie and TV).
    Safe to call even if connections are not initialized yet.
    """
    try:
        movie_db = get_movie_db()
        if movie_db:
            movie_db.close()
            logger.info("Movie database connection closed")
    except Exception as e:
        logger.warning(f"Error closing movie database: {e}")

    try:
        tv_db = get_tv_db()
        if tv_db:
            tv_db.close()
            logger.info("TV database connection closed")
    except Exception as e:
        logger.warning(f"Error closing TV database: {e}")


__all__ = [
    # Database Wrappers
    "get_movie_db",
    "get_tv_db",

    # Clients
    "get_embedding_client",
    "get_stt_client",
    "get_tmdb_client",
    "get_opensubtitles_client",
    "get_rekognition_client",

    # Rate Limiters
    "get_tmdb_rate_limiter",
    "get_opensubtitles_rate_limiter",

    # Utility Functions
    "close_database_connections",
]
