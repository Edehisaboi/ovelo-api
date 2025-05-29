from api.services.database.connection import db_connect, setup_indexes
from ..document.movie import MovieDocumentBuilder
from ..document.tv import TVDocumentBuilder


# Create singleton instances
client, db, movies_collection, tv_collection = db_connect()
movie_document = MovieDocumentBuilder()
tv_document = TVDocumentBuilder()

async def index_database():
    """Initialize the database connection and setup indexes for both collections."""
    await setup_indexes(movies_collection, tv_collection)

__all__ = [
    # Instances
    'client', 'db', 'movies_collection', 'tv_collection',
    # Functions
    'index_database',
    # Classes
    'movie_document', 'tv_document'
]
