from api.services.database.connection import db_connect, setup_indexes
from api.services.database.document import MediaDocument


# Create singleton instances
client, db, movies_collection, tv_collection = db_connect()
media_document = MediaDocument()

async def index_database():
    """Initialize the database connection and setup indexes for both collections."""
    await setup_indexes(movies_collection, tv_collection)

__all__ = [
    # Instances
    'client', 'db', 'movies_collection', 'tv_collection',
    # Functions
    'index_database',
    # Classes
    'media_document'
]
