from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Literal, List


class Settings(BaseSettings):
    """
    Application settings and configuration.
    All settings can be overridden using environment variables or .env file.
    """

    # ============= API Keys and Authentication =============
    """API keys and authentication settings for external services."""
    OPENAI_API_KEY:          str
    TMDB_API_KEY:            str
    OPENSUBTITLES_API_KEY:   str

    # ============= OpenAI Configuration =============
    """OpenAI API and embedding model settings."""
    EMBEDDING_PROVIDER:              str  = "openai"
    OPENAI_EMBEDDING_MODEL:          str  = "text-embedding-3-small"
    OPENAI_EMBEDDING_MAX_TOKENS:     int  = 8192
    OPENAI_EMBEDDING_MAX_RETRIES:    int  = 3
    OPENAI_EMBEDDING_BATCH_SIZE:     int  = 100
    OPENAI_EMBEDDING_WAIT_MIN:       int  = 4
    OPENAI_EMBEDDING_WAIT_MAX:       int  = 10
    OPENAI_EMBEDDING_TIMEOUT:        int  = 30

    # ============= TMDb API Configuration =============
    """TMDb API settings for movie and TV show data."""
    TMDB_BASE_URL:           str = "https://api.themoviedb.org/3"
    TMDB_IMAGE_BASE_URL:     str = "https://image.tmdb.org/t/p"
    TMDB_LANGUAGE:           str = "en-US"
    TMDB_REGION:             str = "US"
    TMDB_RATE_LIMIT:         int = 40
    TMDB_RATE_WINDOW:        int = 10

    # ============= OpenSubtitles Configuration =============
    """OpenSubtitles API settings for subtitle data."""
    OPENSUBTITLES_BASE_URL:          str    = "https://api.opensubtitles.com/api/v1"
    OPENSUBTITLES_RATE_LIMIT:        int    = 40
    OPENSUBTITLES_RATE_WINDOW:       int    = 10
    OPENSUBTITLES_LANGUAGE:          str    = "en"
    OPENSUBTITLES_ORDER_BY:          List[str] = ["download_count"]
    OPENSUBTITLES_ORDER_DIRECTION:   str    = "desc"
    OPENSUBTITLES_TRUSTED_SOURCES:   bool   = True

    # ============= MongoDB Configuration =============
    """MongoDB database connection and collection settings."""
    MONGODB_URL:             str = "mongodb://localhost:27017"
    MONGODB_DB:              str = "moovzmatch"
    MOVIES_COLLECTION:       str = "movies"
    TV_COLLECTION:           str = "tv_shows"

    # ============= Vector Search Configuration =============
    """Vector search and embedding settings for similarity search."""
    # Index names
    MOVIE_INDEX_NAME:        str = "movie_vector_index"
    TV_INDEX_NAME:           str = "tv_vector_index"

    # Embedding paths
    MOVIE_EMBEDDING_PATH:    str = "embedding"
    TV_EMBEDDING_PATH:       str = "embedding"

    # Text paths
    MOVIE_TEXT_PATH:         str = "text"
    TV_TEXT_PATH:            str = "text"

    # Vector dimensions
    MOVIE_NUM_DIMENSIONS:    int = 1536
    TV_NUM_DIMENSIONS:       int = 1536

    # Similarity metrics
    MOVIE_SIMILARITY:        str = "cosine"
    TV_SIMILARITY:           str = "cosine"

    # ============= Search Configuration =============
    """Search and result limiting settings."""
    MOVIE_SEARCH_LIMIT:      int = 3
    TV_SEARCH_LIMIT:         int = 2
    NUM_CANDIDATES:          int = 100
    MAX_RESULTS_PER_PAGE:    int = 10
    DEFAULT_SORT_ORDER:      int = -1  # -1 for descending, 1 for ascending

    """Vector search settings."""
    RAG_TOP_K:          int = 5
    VECTOR_PENALTY:     int = 50
    FULLTEXT_PENALTY:   int = 50

    # ============= Text Processing Configuration =============
    """Text chunking and processing settings."""
    CHUNK_BREAKPOINT_TYPE:   Literal["percentile", "standard_deviation", "interquartile", "gradient"] = "percentile"
    CHUNK_BREAKPOINT_AMOUNT: float = 90.0
    CHUNK_SIZE:              Optional[int] = 8000

    # ============= Caching Configuration =============
    """Cache settings for search results and other data."""
    ENABLE_CACHING:          bool = True
    CACHE_TTL:               int  = 3600  # 1 hour in seconds
    CACHE_MAX_SIZE:          int  = 1000  # Maximum number of items in cache
    SEARCH_CACHE_TTL:        int  = 3600  # 1 hour in seconds
    SEARCH_CACHE_MAX_SIZE:   int  = 100

    # ============= Logging Configuration =============
    """Logging settings for application-wide logging."""
    ENABLE_LOGGING:          bool = True
    LOG_LEVEL:               str  = "INFO"
    LOG_FORMAT:              str  = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DIR:                 str  = "logs"
    LOG_FILE:                str  = "moovzmatch.log"
    LOG_MAX_BYTES:           int  = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT:        int  = 5

    # ============= Feature Flags =============
    """Feature flags to enable/disable specific functionality."""
    INGESTION_ENABLED:       bool = False
    DEBUG_MODE:              bool = False
    ENABLE_RATE_LIMITING:    bool = True

    # Pydantic settings
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )
