from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Literal, List


class Settings(BaseSettings):
    # Embedding settings
    EMBEDDING_PROVIDER:     str = "openai"

    # OpenAI Settings
    OPENAI_API_KEY:         str
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_EMBEDDING_MAX_TOKENS: int = 8192
    OPENAI_EMBEDDING_MAX_RETRIES: int = 3
    OPENAI_EMBEDDING_BATCH_SIZE: int = 100
    OPENAI_EMBEDDING_WAIT_MIN: int = 4
    OPENAI_EMBEDDING_WAIT_MAX: int = 10
    OPENAI_EMBEDDING_WAIT_MULTIPLIER: int = 1

    # Chunking settings
    CHUNK_BREAKPOINT_TYPE:      Literal["percentile", "standard_deviation", "interquartile", "gradient"] = "percentile"
    CHUNK_BREAKPOINT_AMOUNT:    float = 90.0
    CHUNK_SIZE:               Optional[int] = 8000

    # OpenSubtitles settings
    OPENSUBTITLES_API_KEY:  str
    OPENSUBTITLES_BASE_URL: str = "https://api.opensubtitles.com/api/v1"
    OPENSUBTITLES_RATE_LIMIT: int = 40
    OPENSUBTITLES_RATE_WINDOW: int = 10
    OPENSUBTITLES_LANGUAGE: str = "en"
    OPENSUBTITLES_ORDER_BY: List[str] = ["download_count"]
    OPENSUBTITLES_ORDER_DIRECTION: str = "desc"
    OPENSUBTITLES_TRUSTED_SOURCES: bool = True

    # MongoDB configuration
    MONGODB_URL:            str = "mongodb://localhost:27017"
    MONGODB_DB:             str = "moovzmatch"
    MOVIES_COLLECTION:      str = "movies"
    TV_COLLECTION:          str = "tv_shows"

    # MongoDB index settings
    MOVIE_INDEX_NAME:       str = "movie_vector_index"
    TV_INDEX_NAME:          str = "tv_vector_index"

    # Vector embedding paths
    MOVIE_EMBEDDING_PATH:   str = "embedding"
    TV_EMBEDDING_PATH:      str = "embedding"

    # Vector dimensions
    MOVIE_NUM_DIMENSIONS:   int = 1536
    TV_NUM_DIMENSIONS:      int = 1536

    # Similarity metrics
    MOVIE_SIMILARITY:       str = "cosine"
    TV_SIMILARITY:          str = "cosine"

    # Search settings
    MOVIE_SEARCH_LIMIT:     int = 3
    TV_SEARCH_LIMIT:        int = 2
    NUM_CANDIDATES:         int = 100
    SEARCH_CACHE_TTL:       int = 3600  # 1 hour in seconds
    SEARCH_CACHE_MAX_SIZE:  int = 100

    # TMDb API settings
    TMDB_API_KEY:           str
    TMDB_BASE_URL:          str = "https://api.themoviedb.org/3"
    TMDB_IMAGE_BASE_URL:    str = "https://image.tmdb.org/t/p"
    TMDB_LANGUAGE:          str = "en-US"
    TMDB_REGION:            str = "US"
    TMDB_RATE_LIMIT:        int = 40
    TMDB_RATE_WINDOW:       int = 10

    # Database query settings
    MAX_RESULTS_PER_PAGE:   int = 10
    DEFAULT_SORT_FIELD:     str = "release_date"
    DEFAULT_SORT_ORDER:     int = -1  # -1 for descending, 1 for ascending

    # Feature flags
    INGESTION_ENABLED:      bool = False
    DEBUG_MODE:             bool = False
    ENABLE_CACHING:         bool = True
    ENABLE_LOGGING:         bool = True
    ENABLE_RATE_LIMITING:   bool = True

    # Cache settings
    CACHE_TTL:              int = 3600  # 1 hour in seconds
    CACHE_MAX_SIZE:         int = 1000  # Maximum number of items in cache

    # Logging settings
    LOG_LEVEL:              str = "INFO"
    LOG_FORMAT:             str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DIR:                str = "logs"
    LOG_FILE:               str = "moovzmatch.log"
    LOG_MAX_BYTES:          int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT:       int = 5

    # Pydantic settings
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )
