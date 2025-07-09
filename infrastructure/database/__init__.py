from typing import Optional
from threading import Lock

from .mongodb import MongoClientWrapper
from .queries import search_by_title, vector_search
from .indexes import MongoIndex

# Create singleton instances with thread safety
from application.models.media import MovieDetails, TVDetails
from application.core.config import settings
from application.core.logging import get_logger

logger = get_logger(__name__)

class DatabaseManager:
    """Thread-safe singleton manager for database connections."""
    
    _instance: Optional['DatabaseManager'] = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._movie_db: Optional[MongoClientWrapper] = None
        self._tv_db: Optional[MongoClientWrapper] = None
        self._lock = Lock()
        self._initialized = True
    
    def movie_db(self) -> MongoClientWrapper:
        """Get a singleton instance of the movie database wrapper."""
        if self._movie_db is None:
            with self._lock:
                if self._movie_db is None:
                    try:
                        self._movie_db = MongoClientWrapper(
                            model=MovieDetails,
                            collection_name=settings.MOVIES_COLLECTION,
                            database_name=settings.MONGODB_DB,
                            mongodb_uri=settings.MONGODB_URL
                        )
                        # Initialize indexes for the collection
                        self._movie_db.initialize_indexes()
                        logger.info("Movie database connection initialized with indexes")
                    except Exception as e:
                        logger.error(f"Failed to initialize movie database: {e}")
                        raise
        return self._movie_db
    
    def tv_db(self) -> MongoClientWrapper:
        """Get a singleton instance of the TV database wrapper."""
        if self._tv_db is None:
            with self._lock:
                if self._tv_db is None:
                    try:
                        self._tv_db = MongoClientWrapper(
                            model=TVDetails,
                            collection_name=settings.TV_COLLECTION,
                            database_name=settings.MONGODB_DB,
                            mongodb_uri=settings.MONGODB_URL
                        )
                        # Initialize indexes for the collection
                        self._tv_db.initialize_indexes()
                        logger.info("TV database connection initialized with indexes")
                    except Exception as e:
                        logger.error(f"Failed to initialize TV database: {e}")
                        raise
        return self._tv_db
    
    def close_all(self):
        """Close all database connections."""
        with self._lock:
            if self._movie_db:
                try:
                    self._movie_db.close()
                    logger.info("Movie database connection closed")
                except Exception as e:
                    logger.error(f"Error closing movie database: {e}")
                finally:
                    self._movie_db = None
            
            if self._tv_db:
                try:
                    self._tv_db.close()
                    logger.info("TV database connection closed")
                except Exception as e:
                    logger.error(f"Error closing TV database: {e}")
                finally:
                    self._tv_db = None

# Global database manager instance
_db_manager = DatabaseManager()

def movie_db() -> MongoClientWrapper:
    """Get a singleton instance of the movie database wrapper."""
    return _db_manager.movie_db()

def tv_db() -> MongoClientWrapper:
    """Get a singleton instance of the TV database wrapper."""
    return _db_manager.tv_db()

def close_database_connections():
    """Close all database connections. Useful for cleanup."""
    _db_manager.close_all()

__all__ = [
    "MongoClientWrapper",
    "MongoIndex",

    "search_by_title",
    "vector_search",

    "movie_db",
    "tv_db",

    "close_database_connections",
    "DatabaseManager"
] 