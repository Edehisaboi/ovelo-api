from .tmdb import TMDbService
from application.core.resources import tmdb_client

# Create singleton instance
tmdb_service = TMDbService(tmdb_client)

__all__ = [
    "TMDbService",
    "tmdb_service"
] 