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
from infrastructure.database import tv_db, movie_db

# --- HTTP Client Singleton ---

@lru_cache()
def get_http_client() -> httpx.AsyncClient:
    """Return a singleton Async HTTP client instance."""
    return httpx.AsyncClient()

# --- Database Wrappers ---

@lru_cache()
def get_movie_db():
    """Return a singleton movie database wrapper instance."""
    return movie_db()

@lru_cache()
def get_tv_db():
    """Return a singleton TV database wrapper instance."""
    return tv_db()

# --- Embeddings & STT Clients ---

@lru_cache()
def get_embedding_client() -> EmbeddingClient:
    """Return a singleton EmbeddingClient instance."""
    return EmbeddingClient()

@lru_cache()
def get_stt_client() -> OpenAISTT:
    """Return a singleton OpenAI STT client instance."""
    return OpenAISTT()

# --- TMDb Client & Rate Limiter ---

@lru_cache()
def get_tmdb_rate_limiter() -> RateLimiter:
    """Return a singleton rate limiter for TMDb API."""
    return RateLimiter.from_settings("tmdb")

@lru_cache()
def get_tmdb_client() -> TMDbClient:
    """Return a singleton TMDb client instance."""
    return TMDbClient(
        api_key      = settings.TMDB_API_KEY,
        http_client  = get_http_client(),
        rate_limiter = get_tmdb_rate_limiter(),
        base_url     = settings.TMDB_BASE_URL
    )

# --- OpenSubtitles Client & Rate Limiter ---

@lru_cache()
def get_opensubtitles_rate_limiter() -> RateLimiter:
    """Return a singleton rate limiter for OpenSubtitles API."""
    return RateLimiter.from_settings("opensubtitles")

@lru_cache()
def get_opensubtitles_client() -> OpenSubtitlesClient:
    """Return a singleton OpenSubtitles client instance."""
    return OpenSubtitlesClient(
        api_key      = settings.OPENSUBTITLES_API_KEY,
        http_client  = get_http_client(),
        rate_limiter = get_opensubtitles_rate_limiter(),
        base_url     = settings.OPENSUBTITLES_BASE_URL
    )

# --- Rekognition Client ---

@lru_cache()
def get_rekognition_client() -> RekognitionClient:
    """Return a singleton Rekognition client instance."""
    return RekognitionClient()
