from .tmdb import TMDbService
from application.core.dependencies import get_tmdb_client

# Create singleton instance
tmdb_service = TMDbService(get_tmdb_client())

__all__ = [
    "TMDbService",
    "tmdb_service"
] 