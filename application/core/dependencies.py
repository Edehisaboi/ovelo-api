import threading

import asyncio
import httpx
from functools import lru_cache
from typing import Any, Optional

from application.core.config import settings
from external.clients import (
    OpenSubtitlesClient,
    TMDbClient,
    EmbeddingClient,
    AWSTranscribeRealtimeSTTClient,
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
def aws_stt_client() -> AWSTranscribeRealtimeSTTClient:
    return AWSTranscribeRealtimeSTTClient()

# Rekognition client singleton (async-safe, no lru_cache on async functions)
_rekognition_instance: Optional[RekognitionClient] = None
_rekognition_lock = asyncio.Lock()

async def rekognition_client() -> RekognitionClient:
    global _rekognition_instance
    async with _rekognition_lock:
        if _rekognition_instance is None:
            client = RekognitionClient()
            await client.__aenter__()
            _rekognition_instance = client
        return _rekognition_instance

@lru_cache()
def _mongo_manager_singleton():
    from infrastructure.database.mongodb import MongoCollectionsManager
    lock = asyncio.Lock()
    instance: dict[str, MongoCollectionsManager | None] = {"manager": None}

    async def get_instance():
        async with lock:
            if instance["manager"] is None:
                instance["manager"] = await create_mongo_collections_manager(
                    database_name=settings.MONGODB_DB,
                    mongodb_uri=settings.MONGODB_URL,
                    embedding_client=embedding_client(),
                    initialize_indexes=False
                )
            return instance["manager"]
    return get_instance

mongo_manager = _mongo_manager_singleton()

@lru_cache()
def _ws_connection_manager_singleton():
    """Thread-safe singleton factory for ConnectionManager to manage all WebSocket connections."""
    # Use a threading lock to guard initialization across event loops/threads
    instance: dict[str, Any] = {"manager": None}
    init_lock = threading.Lock() if threading else None

    def get_instance():
        nonlocal instance
        if instance["manager"] is not None:
            return instance["manager"]

        # Double-checked locking
        if init_lock:
            with init_lock:
                if instance["manager"] is None:
                    from application.api.v1.ws_manager import ConnectionManager
                    instance["manager"] = ConnectionManager()
                    logger.info("ConnectionManager singleton instance created")
        else:
            # Fallback without lock
            from application.api.v1.ws_manager import ConnectionManager
            instance["manager"] = ConnectionManager()
            logger.info("ConnectionManager singleton instance created (no lock)")

        return instance["manager"]

    return get_instance

ws_connection_manager = _ws_connection_manager_singleton()

async def close_database_connections():
    try:
        manager = await mongo_manager()
        if manager:
            await manager.close()
            _mongo_manager_singleton.cache_clear()
        logger.info("Database connections closed.")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")

async def close_websocket_connections():
    """Close all active WebSocket connections."""
    try:
        manager = ws_connection_manager()
        if manager:
            # Close all active connections
            connection_ids = list(manager.active_connections.keys())
            for conn_id in connection_ids:
                await manager.close_connection(conn_id)
            logger.info(f"Closed {len(connection_ids)} WebSocket connections")
    except Exception as e:
        logger.error(f"Error closing WebSocket connections: {e}")

async def close_rekognition_client():
    """Properly close and clear the single RekognitionClient instance."""
    global _rekognition_instance
    try:
        async with _rekognition_lock:
            if _rekognition_instance is not None:
                await _rekognition_instance.__aexit__(None, None, None)
                _rekognition_instance = None
        logger.info("Rekognition client closed.")
    except Exception as e:
        logger.error(f"Error closing Rekognition client: {e}")

__all__ = [
    "mongo_manager",
    "ws_connection_manager",
    "embedding_client",
    "aws_stt_client",
    "tmdb_client",
    "opensubtitles_client",
    "rekognition_client",
    "close_database_connections",
    "close_websocket_connections",
    "close_rekognition_client"
]
