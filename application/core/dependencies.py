import asyncio
import httpx
from functools import lru_cache

from application.core.config import settings
from external.clients import (
    OpenSubtitlesClient,
    TMDbClient,
    EmbeddingClient,
    OpenAISTT,
    RekognitionClient
)
from application.utils.rate_limiter import RateLimiter
from application.core.logging import get_logger
from infrastructure.database import MongoCollectionsManager, create_mongo_collections_manager

logger = get_logger(__name__)



@lru_cache()
def get_embedding_client() -> EmbeddingClient:
    return EmbeddingClient()

@lru_cache()
def get_tmdb_client() -> TMDbClient:
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
    return OpenAISTT()

@lru_cache()
def get_rekognition_client() -> RekognitionClient:
    return RekognitionClient()


# ---- Async Singleton for MongoCollectionsManager ----

_mongo_manager_instance = None
_mongo_manager_lock = asyncio.Lock()

async def get_mongo_manager() -> MongoCollectionsManager:
    """
    Async singleton for MongoCollectionsManager.
    Ensures only one instance is created and reused.
    """
    global _mongo_manager_instance
    async with _mongo_manager_lock:
        if _mongo_manager_instance is None:
            _mongo_manager_instance = await create_mongo_collections_manager(
                database_name=settings.MONGODB_DB,
                mongodb_uri=settings.MONGODB_URL,
                embedding_client=get_embedding_client()
            )
    return _mongo_manager_instance



# ---- Close Database Connections ----

async def close_database_connections():
    """Close all database connections (if needed)."""
    try:
        global _mongo_manager_instance
        if _mongo_manager_instance:
            await _mongo_manager_instance.close()
            _mongo_manager_instance = None
        logger.info("Database connections closed.")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


__all__ = [
    # MongoDB Manager
    "get_mongo_manager",

    # Clients
    "get_embedding_client",
    "get_stt_client",
    "get_tmdb_client",
    "get_opensubtitles_client",
    "get_rekognition_client",

    # Utility Functions
    "close_database_connections",
]
