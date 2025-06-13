from config import settings
from .mongo import MongoClientWrapper
from api.services.tmdb.model import MovieDetails, TVDetails

# Create singleton instances for movies and TV shows
movie_db = MongoClientWrapper(
    model=MovieDetails,  # This will be overridden by the document builder
    collection_name=settings.MOVIES_COLLECTION
)

tv_db = MongoClientWrapper(
    model=TVDetails,  # This will be overridden by the document builder
    collection_name=settings.TV_COLLECTION
)


# Export all necessary components
__all__ = [
    # Classes
    'MongoClientWrapper',
    
    # Database instances
    'movie_db',
    'tv_db',
]
