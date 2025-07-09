from dotenv import load_dotenv
load_dotenv()

from .logging import get_logger
from .dependencies import (
    get_movie_db,
    get_tv_db,
    get_embedding_client,
    get_tmdb_client,
    get_opensubtitles_client,
    get_stt_client,
    get_rekognition_client
)

# Singleton instances for application-wide use
movie_db             = get_movie_db()
tv_db                = get_tv_db()
embedding_client     = get_embedding_client()
stt_client           = get_stt_client()
tmdb_client          = get_tmdb_client()
opensubtitles_client = get_opensubtitles_client()
rekognition_client   = get_rekognition_client()

__all__ = [
    # Database Wrappers
    "movie_db",
    "tv_db",

    # Embeddings
    "embedding_client",

    # STT Client
    "stt_client",

    # TMDb
    "tmdb_client",

    # OpenSubtitles
    "opensubtitles_client",

    # Rekognition
    "rekognition_client",

    # Logging
    "get_logger",
]
