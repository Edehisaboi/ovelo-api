from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Embedding settings
    EMBEDDING_PROVIDER:     str = "openai"

    # OpenAI Settings
    OPENAI_API_KEY:         str
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # OpenSubtitles settings
    OPENSUBTITLES_API_KEY:  str

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
    MOVIE_SEARCH_LIMIT:     int = 20
    TV_SEARCH_LIMIT:        int = 20
    NUM_CANDIDATES:         int = 100

    # TMDb API settings
    TMDB_API_KEY:           str = "your_api_key_here"
    TMDB_BASE_URL:          str = "https://api.themoviedb.org/3"
    TMDB_IMAGE_BASE_URL:    str = "https://image.tmdb.org/t/p"
    TMDB_LANGUAGE:          str = "en-US"
    TMDB_REGION:            str = "US"

    # Database query settings
    MAX_RESULTS_PER_PAGE:   int = 20
    DEFAULT_SORT_FIELD:     str = "release_date"
    DEFAULT_SORT_ORDER:     int = -1  # -1 for descending, 1 for ascending

    # Feature flags
    INGESTION_ENABLED:      bool = False
    DEBUG_MODE:             bool = False
    ENABLE_CACHING:         bool = True
    ENABLE_LOGGING:         bool = True

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
