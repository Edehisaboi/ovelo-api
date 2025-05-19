from .db_index import create_movie_indexes, create_tv_indexes
from pymongo.mongo_client import MongoClient
from pymongo.collection import Collection
from config import Settings
from config.logging import get_logger

# Get logger for this module
logger = get_logger(__name__)

def db_connect():
    """
    Connect to the MongoDB database and get collections.
    Returns:
        tuple: (client, db, movies_collection, tv_collection) MongoDB connection objects
    """
    client = MongoClient(Settings.MONGODB_URL)
    db = client[Settings.MONGODB_DB]
    movies_collection = db[Settings.MOVIES_COLLECTION]
    tv_collection = db[Settings.TV_COLLECTION]
    
    try:
        # Test the connection
        movies_collection.client.admin.command('ping')
        logger.info("Database connection successful.")
        return client, db, movies_collection, tv_collection
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise

async def setup_indexes(movies_collection: Collection, tv_collection: Collection):
    """
    Set up indexes for both movie and TV show collections.
    Args:
        movies_collection: MongoDB collection for movies
        tv_collection: MongoDB collection for TV shows
    """
    logger.info("Setting up movie collection indexes...")
    await create_movie_indexes(movies_collection)
    
    logger.info("Setting up TV show collection indexes...")
    await create_tv_indexes(tv_collection)

__all__ = ['db_connect', 'setup_indexes']
