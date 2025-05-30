from functools import lru_cache

import httpx
from openai import OpenAI
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from config import Settings, settings
from api.clients import EmbeddingClient, OpenSubtitlesClient, TMDbClient
from api.services.rateLimiting.limiter import RateLimiter


@lru_cache()
def get_settings() -> Settings:
    """Get a singleton settings instance."""
    return Settings()


@lru_cache()
def get_http_client() -> httpx.AsyncClient:
    """Get a singleton HTTP client instance."""
    return httpx.AsyncClient()


@lru_cache()
def get_mongo_client() -> MongoClient:
    """Get a singleton MongoDB client instance."""
    return MongoClient(settings.MONGODB_URL)


@lru_cache()
def get_mongo_db() -> Database:
    """Get the MongoDB database instance."""
    return get_mongo_client()[settings.MONGODB_DB]


@lru_cache()
def get_movies_collection() -> Collection:
    """Get the movies collection from MongoDB."""
    return get_mongo_db()[settings.MOVIES_COLLECTION]


@lru_cache()
def get_tv_collection() -> Collection:
    """Get the TV shows collection from MongoDB."""
    return get_mongo_db()[settings.TV_COLLECTION]


@lru_cache()
def get_openai_client() -> OpenAI:
    """Get a singleton OpenAI client instance."""
    return OpenAI(api_key=settings.OPENAI_API_KEY)


@lru_cache()
def get_embedding_client() -> EmbeddingClient:
    """Get a singleton EmbeddingClient instance."""
    return EmbeddingClient(client=get_openai_client())


@lru_cache()
def get_tmdb_client() -> TMDbClient:
    """Get a singleton TMDb client instance."""
    return TMDbClient(
        api_key=settings.TMDB_API_KEY,
        http_client=get_http_client(),
        rate_limiter=get_tmdb_rate_limiter()
    )


@lru_cache()
def get_opensubtitles_client() -> OpenSubtitlesClient:
    """Get a singleton OpenSubtitles client instance."""
    return OpenSubtitlesClient(
        api_key=settings.OPENSUBTITLES_API_KEY,
        rate_limiter=get_opensubtitles_rate_limiter()
    )


@lru_cache()
def get_tmdb_rate_limiter() -> RateLimiter:
    """Get a singleton rate limiter for TMDb API."""
    return RateLimiter.from_settings(settings, "tmdb")


@lru_cache()
def get_opensubtitles_rate_limiter() -> RateLimiter:
    """Get a singleton rate limiter for OpenSubtitles API."""
    return RateLimiter.from_settings(settings, "opensubtitles")
