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
from infrastructure.database import create_mongo_collections_manager

logger = get_logger(__name__)

@lru_cache()
def embedding_client() -> EmbeddingClient:
    return EmbeddingClient()

@lru_cache()
def tmdb_client() -> TMDbClient:
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
def opensubtitles_client() -> OpenSubtitlesClient:
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
def stt_client() -> OpenAISTT:
    return OpenAISTT(
        api_key=settings.OPENAI_API_KEY,
        http_client=httpx.AsyncClient(),
        base_url=settings.OPENAI_STT_BASE_URL
    )

@lru_cache()
def rekognition_client() -> RekognitionClient:
    return RekognitionClient()

@lru_cache()
def _mongo_manager_singleton():
    lock = asyncio.Lock()
    instance = {"manager": None}

    async def get_instance():
        async with lock:
            if instance["manager"] is None:
                instance["manager"] = await create_mongo_collections_manager(
                    database_name=settings.MONGODB_DB,
                    mongodb_uri=settings.MONGODB_URL,
                    embedding_client=embedding_client()
                )
            return instance["manager"]
    return get_instance

mongo_manager = _mongo_manager_singleton()

async def close_database_connections():
    try:
        manager = await mongo_manager()
        if manager:
            await manager.close()
            _mongo_manager_singleton.cache_clear()
        logger.info("Database connections closed.")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")

__all__ = [
    "mongo_manager",
    "embedding_client",
    "stt_client",
    "tmdb_client",
    "opensubtitles_client",
    "rekognition_client",
    "close_database_connections",
]
