from api.services.database.connection import db_connect, setup_indexes


# Create singleton instances
client, db, movies_collection, tv_collection = db_connect()

async def index_database():
    """Initialize the database connection and setup indexes for both collections."""
    await setup_indexes(movies_collection, tv_collection)

__all__ = ['client', 'db', 'movies_collection', 'tv_collection', 'index_database']
