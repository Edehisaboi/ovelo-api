from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

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

    # ============= Comet Configuration =============
    """Comet ML settings for tracking."""
    COMET_API_KEY:           str
    COMET_PROJECT:           str = "Moovio-API"

    # ============= OpenAI Configuration =============
    """LLM settings."""
    OPENAI_LLM_MODEL:        str = "gpt-4.1-2025-04-14"
    LLM_TEMPERATURE:         float = 0

    """OpenAI API and embedding model settings."""
    EMBEDDING_PROVIDER:              str  = "openai"
    OPENAI_EMBEDDING_MODEL:          str  = "text-embedding-3-small"
    OPENAI_TOKEN_ENCODING:           str  = "cl100k_base"
    OPENAI_EMBEDDING_MAX_TOKENS:     int  = 8192
    OPENAI_EMBEDDING_MAX_RETRIES:    int  = 3
    OPENAI_EMBEDDING_BATCH_SIZE:     int  = 100
    OPENAI_EMBEDDING_WAIT_MIN:       int  = 4
    OPENAI_EMBEDDING_WAIT_MAX:       int  = 10
    OPENAI_EMBEDDING_TIMEOUT:        int  = 30

    # ========== AWS Rekognition Configuration =======
    AWS_ACCESS_KEY_ID:          str
    AWS_SECRET_ACCESS_KEY:      str
    AWS_REGION:                 str = "us-east-1"
    AWS_MAX_IMAGE_BYTES:        int = 5 * 1024 * 1024  # 5 MB limit for Rekognition images

    """AWS Realtime Speech-to-Text Configuration."""
    AWS_STT_LANGUAGE: str = "en-US"  # Default language for AWS STT
    AWS_STT_INPUT_AUDIO_FORMAT: str = "pcm16"

    # ============= TMDb API Configuration =============
    """TMDb API settings for movie and TV show data."""
    TMDB_BASE_URL:           str = "https://api.themoviedb.org/3"
    TMDB_IMAGE_BASE_URL:     str = "https://image.tmdb.org/t/p/w500"
    TMDB_LANGUAGE:           str = "en-US"
    TMDB_REGION:             str = "US"
    TMDB_RATE_LIMIT:         int = 20
    TMDB_RATE_WINDOW:        int = 1
    TMDB_ALLOWED_LANGUAGE:   str = "en"

    YOUTUBE_BASE_URL:        str = "https://www.youtube.com/watch?v="

    # ============= OpenSubtitles Configuration =============
    """OpenSubtitles API settings for subtitle data."""
    OPENSUBTITLES_BASE_URL:          str    = "https://api.opensubtitles.com/api/v1"
    OPENSUBTITLES_RATE_LIMIT:        int    = 5
    OPENSUBTITLES_RATE_WINDOW:       int    = 1
    OPENSUBTITLES_LANGUAGE:          str    = "en"
    OPENSUBTITLES_ORDER_BY:          str    = "download_count"
    OPENSUBTITLES_ORDER_DIRECTION:   str    = "desc"

    # ============= MongoDB Configuration =============
    """MongoDB database connection and collection settings."""
    MONGODB_URL:             str
    MONGODB_DB:              str = "moovzmatch"

    MOVIES_COLLECTION:       str = "movies"
    MOVIE_CHUNKS_COLLECTION: str = "movie_chunks"
    MOVIE_WATCH_PROVIDERS_COLLECTION: str = "movie_watch_providers"

    TV_COLLECTION:           str = "tv_shows"
    TV_SEASONS_COLLECTION:   str = "tv_seasons"
    TV_EPISODES_COLLECTION:  str = "tv_episodes"
    TV_CHUNKS_COLLECTION:    str = "tv_chunks"
    TV_WATCH_PROVIDERS_COLLECTION: str = "tv_watch_providers"

    # ============= Vector Search Configuration =============
    """Vector search and embedding settings for similarity search."""
    # Vector Index names
    MOVIE_VECTOR_INDEX_NAME:        str = "movie_vector_index"
    TV_VECTOR_INDEX_NAME:           str = "tv_vector_index"

    # Full-text Index names
    MOVIE_FULLTEXT_INDEX_NAME:      str = f"{MOVIE_CHUNKS_COLLECTION}_fulltext_index"
    TV_FULLTEXT_INDEX_NAME:         str = f"{TV_CHUNKS_COLLECTION}_fulltext_index"

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
    MOVIE_SIMILARITY:        str = "dotProduct"
    TV_SIMILARITY:           str = "dotProduct"

    # ============= Search Configuration =============
    """Search and result limiting settings."""
    MOVIE_SEARCH_LIMIT:      int = 3
    TV_SEARCH_LIMIT:         int = 2
    NUM_CANDIDATES:          int = 100
    MAX_RESULTS_PER_PAGE:    int = 10
    DEFAULT_SORT_ORDER:      int = -1  # -1 for descending, 1 for ascending

    """Vector search settings."""
    RAG_TOP_K:              int = 5
    VECTOR_PENALTY:         int = 30
    FULLTEXT_PENALTY:       int = 20
    OVERSAMPLING_FACTOR:    int = 5 # This times RAG_TOP_K is the number of candidates chosen at each step

    # ============= Text Processing Configuration =============
    """Text chunking and processing settings."""
    CHUNK_BREAKPOINT_TYPE:    Literal["percentile", "standard_deviation", "interquartile", "gradient"] = "percentile"
    CHUNK_BREAKPOINT_AMOUNT:  float = 95.0
    CHUNK_SIZE:               int = 160 # The max is 8191
    CHUNK_BUFFER_SIZE:        int = 1
    MIN_CHUNK_WORDS:          int = 5
    CHUNK_OVERLAP_PERCENT:    float = 0.15  # 15% overlap between chunks

    # ============= Batch Processing Configuration =============
    """Batch processing settings for TV show extraction."""
    TV_EXTRACTION_BATCH_SIZE: int = OPENSUBTITLES_RATE_LIMIT - 2   # Number of episodes to process concurrently
    TV_EXTRACTION_BATCH_DELAY: float = 1.0  # Delay between batches in seconds

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
    INGESTION_ENABLED:       bool = True
    DEBUG_MODE:              bool = False
    ENABLE_RATE_LIMITING:    bool = True

    MAX_INGESTION_ITEMS:    int = 1  # Maximum number of items to ingest per search

    # ============= vRecognition Config =============
    MAX_RETRIEVAL_SCORE:         float = \
    (1 / (VECTOR_PENALTY + 1)) + (1 / (FULLTEXT_PENALTY + 1))

    ACTOR_MATCH_BONUS:          float = 0.10 * MAX_RETRIEVAL_SCORE  # Actor bonus will add 10% of the maximum retrieval score for each matched actor
    MIN_SCORE_GATE:             float = 0.50 * MAX_RETRIEVAL_SCORE  # Minimum score to consider a match
    ACCEPTANCE_THRESHOLD:       float = 1.10 * MAX_RETRIEVAL_SCORE  # Threshold for accepting a match immediately

    # Pydantic settings
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )


# Create singleton instance
settings = Settings()