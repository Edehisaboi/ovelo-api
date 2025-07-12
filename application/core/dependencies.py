from functools import lru_cache
import httpx

from application.core.config import settings
from external.clients import (
    OpenSubtitlesClient,
    TMDbClient,
    EmbeddingClient,
    OpenAISTT,
    RekognitionClient
)
from application.utils.rate_limiter import RateLimiter
from application.models import MovieDetails, TVDetails
from application.core.logging import get_logger
from infrastructure.database.mongodb import MongoClientWrapper, create_mongo_client_wrapper

logger = get_logger(__name__)


@lru_cache()
def get_embedding_client() -> EmbeddingClient:
    """Return a singleton EmbeddingClient instance."""
    return EmbeddingClient()


@lru_cache()
def get_tmdb_client() -> TMDbClient:
    """Return a singleton TMDbClient instance."""
    from application.utils.rate_limiter import RateLimitConfig
    return TMDbClient(
        api_key=settings.TMDB_API_KEY,
        http_client=httpx.AsyncClient(),
        base_url=settings.TMDB_BASE_URL,
        rate_limiter=RateLimiter(
            RateLimitConfig(
                rate_limit=settings.TMDB_RATE_LIMIT,
                rate_window=settings.TMDB_RATE_WINDOW,
                enabled=settings.ENABLE_RATE_LIMITING
            )
        )
    )


@lru_cache()
def get_opensubtitles_client() -> OpenSubtitlesClient:
    """Return a singleton OpenSubtitlesClient instance."""
    from application.utils.rate_limiter import RateLimitConfig
    return OpenSubtitlesClient(
        api_key=settings.OPENSUBTITLES_API_KEY,
        http_client=httpx.AsyncClient(follow_redirects=True),
        base_url=settings.OPENSUBTITLES_BASE_URL,
        rate_limiter=RateLimiter(
            RateLimitConfig(
                rate_limit=settings.OPENSUBTITLES_RATE_LIMIT,
                rate_window=settings.OPENSUBTITLES_RATE_WINDOW,
                enabled=settings.ENABLE_RATE_LIMITING
            )
        )
    )


@lru_cache()
def get_stt_client() -> OpenAISTT:
    """Return a singleton OpenAISTT instance."""
    return OpenAISTT()


@lru_cache()
def get_rekognition_client() -> RekognitionClient:
    """Return a singleton RekognitionClient instance."""
    return RekognitionClient()


@lru_cache()
async def get_movie_db() -> MongoClientWrapper:
    """Return a singleton MongoClientWrapper instance for movies."""
    client = await create_mongo_client_wrapper(
        model=MovieDetails,
        collection_name=settings.MOVIES_COLLECTION,
        database_name=settings.MONGODB_DB,
        mongodb_uri=settings.MONGODB_URL,
        embedding_client=get_embedding_client()
    )
    await client.initialize_indexes()
    return client


@lru_cache()
async def get_tv_db() -> MongoClientWrapper:
    """Return a singleton MongoClientWrapper instance for TV shows."""
    client = await create_mongo_client_wrapper(
        model=TVDetails,
        collection_name=settings.TV_COLLECTION,
        database_name=settings.MONGODB_DB,
        mongodb_uri=settings.MONGODB_URL,
        embedding_client=get_embedding_client()
    )
    await client.initialize_indexes()
    return client


async def close_database_connections():
    """Close all database connections."""
    try:
        # Get instances and close them
        movie_client = await get_movie_db()
        tv_client = await get_tv_db()
        
        await movie_client.close()
        await tv_client.close()
        
        logger.info("Database connections closed.")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


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

    # Utility Functions
    "close_database_connections",
]
