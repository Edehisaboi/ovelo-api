from config import settings
from .mongo import MongoClientWrapper
from .index import setup_indexes
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


async def index_database():
    """Initialize the database indexes for both collections."""
    await setup_indexes()


# Export all necessary components
__all__ = [
    # Classes
    'MongoClientWrapper',
    
    # Database instances
    'movie_db',
    'tv_db',
    
    # Functions
    'index_database'
]
