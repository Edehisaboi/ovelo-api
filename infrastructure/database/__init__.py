from .mongodb import MongoClientWrapper
from .queries import search_by_title, vector_search
from .indexes import MongoIndex

# Create singleton instances
from application.models.media import MovieDetails, TVDetails
from application.core.config import settings

movie_db = None
tv_db = None

def _get_movie_db():
    global movie_db
    if movie_db is None:
        from infrastructure.database.mongodb import MongoClientWrapper
        movie_db = MongoClientWrapper(
            model=MovieDetails,
            collection_name=settings.MOVIES_COLLECTION
        )
    return movie_db

def _get_tv_db():
    global tv_db
    if tv_db is None:
        from infrastructure.database.mongodb import MongoClientWrapper
        tv_db = MongoClientWrapper(
            model=TVDetails,
            collection_name=settings.TV_COLLECTION
        )
    return tv_db

__all__ = [
    "MongoClientWrapper",
    "MongoIndex",

    "search_by_title",
    "vector_search",

    "_get_movie_db",
    "_get_tv_db"
] 