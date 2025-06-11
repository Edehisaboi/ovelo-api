import time

from pymongo import ASCENDING, TEXT
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
from pymongo.operations import IndexModel, SearchIndexModel

from config import settings, get_logger, get_movies_collection, get_tv_collection

logger = get_logger(__name__)


async def _create_and_wait(collection: Collection, model: SearchIndexModel):
    """
    Creates a vector search index and waits until it's ready.
    Skips creation if the index already exists.
    """
    index_name = model.name

    # Check if index already exists
    existing = list(collection.list_search_indexes())
    if any(ix.get("name") == index_name for ix in existing):
        logger.info(f"Search index '{index_name}' already exists. Skipping creation.")
        return

    try:
        created_name = collection.create_search_index(model=model, name=index_name)
        logger.info(f"Search index '{created_name}' is building...")

        while True:
            index_info = list(collection.list_search_indexes(created_name))
            if index_info and index_info[0].get("queryable") is True:
                break
            time.sleep(3)

        logger.info(f"Search index '{created_name}' is ready for querying.")

    except PyMongoError as e:
        logger.error(f"Failed to create search index '{index_name}': {str(e)}")
        raise


async def _create_movie_indexes(collection: Collection):
    """
    Creates all necessary indexes for efficient querying of movies.
    Includes vector search indexes for embeddings and traditional indexes for common queries.
    """
    # Vector search index for movie embeddings
    movie_index_model = SearchIndexModel(
        definition={
            "fields": [
                {
                    "type":          "vector",
                    "path":          settings.MOVIE_EMBEDDING_PATH,
                    "numDimensions": settings.MOVIE_NUM_DIMENSIONS,
                    "similarity":    settings.MOVIE_SIMILARITY
                }
            ]
        },
        name=settings.MOVIE_INDEX_NAME,
        type="vectorSearch"
    )

    # Traditional indexes for movie-specific queries
    movie_indexes = [
        # Unique indexes for identifiers
        IndexModel([("tmdb_id", ASCENDING)], unique=True),
        IndexModel([("external_ids.imdb_id", ASCENDING)], unique=True, sparse=True),
        
        # Text indexes for searchable fields
        IndexModel([
            ("title", TEXT),
            ("original_title", TEXT),
            ("tagline", TEXT)
        ], name="movie_text_search"),
        
        # Compound indexes for common query patterns
        IndexModel([
            ("status", ASCENDING),
            ("release_date", ASCENDING)
        ], name="movie_status_date"),
        
        # Array indexes for filtering
        IndexModel([("genres", ASCENDING)], name="movie_genres"),
        IndexModel([("spoken_languages.name", ASCENDING)], name="movie_languages"),
        IndexModel([("origin_country", ASCENDING)], name="movie_countries"),
        
        # Cast and crew indexes
        IndexModel([("cast.name", ASCENDING)], name="movie_cast"),
        IndexModel([("crew.name", ASCENDING)], name="movie_crew"),
        
        # Watch provider indexes
        IndexModel([("watch_providers.flatrate.provider_name", ASCENDING)], name="movie_providers")
    ]

    try:
        # Create traditional indexes
        collection.create_indexes(movie_indexes)
        logger.info("Created movie traditional indexes successfully.")

        # Create vector search index
        await _create_and_wait(collection, movie_index_model)

    except PyMongoError as e:
        logger.error(f"Failed to create movie indexes: {str(e)}")
        raise


async def _create_tv_indexes(collection: Collection):
    """
    Creates all necessary indexes for efficient querying of TV shows.
    Includes vector search indexes for embeddings and traditional indexes for common queries.
    """
    # Vector search index for TV show embeddings
    tv_index_model = SearchIndexModel(
        definition={
            "fields": [
                {
                    "type":          "vector",
                    "path":          settings.TV_EMBEDDING_PATH,
                    "numDimensions": settings.TV_NUM_DIMENSIONS,
                    "similarity":    settings.TV_SIMILARITY
                }
            ]
        },
        name=settings.TV_INDEX_NAME,
        type="vectorSearch"
    )

    # Traditional indexes for TV show-specific queries
    tv_indexes = [
        # Unique indexes for identifiers
        IndexModel([("tmdb_id", ASCENDING)], unique=True),
        IndexModel([("external_ids.imdb_id", ASCENDING)], unique=True, sparse=True),
        
        # Text indexes for searchable fields
        IndexModel([
            ("name", TEXT),
            ("original_name", TEXT),
            ("tagline", TEXT)
        ], name="tv_text_search"),
        
        # Compound indexes for common query patterns
        IndexModel([
            ("status", ASCENDING),
            ("first_air_date", ASCENDING)
        ], name="tv_status_date"),
        
        # Array indexes for filtering
        IndexModel([("genres", ASCENDING)], name="tv_genres"),
        IndexModel([("spoken_languages.name", ASCENDING)], name="tv_languages"),
        IndexModel([("origin_country", ASCENDING)], name="tv_countries"),
        
        # Cast and crew indexes
        IndexModel([("cast.name", ASCENDING)], name="tv_cast"),
        IndexModel([("crew.name", ASCENDING)], name="tv_crew"),
        
        # Season and episode indexes
        IndexModel([("seasons.season_number", ASCENDING)], name="tv_seasons"),
        IndexModel([
            ("seasons.episodes.episode_number", ASCENDING),
            ("seasons.season_number", ASCENDING)
        ], name="tv_episodes"),
        
        # Watch provider indexes
        IndexModel([("watch_providers.flatrate.provider_name", ASCENDING)], name="tv_providers")
    ]

    try:
        # Create traditional indexes
        collection.create_indexes(tv_indexes)
        logger.info("Created TV show traditional indexes successfully.")

        # Create vector search index
        await _create_and_wait(collection, tv_index_model)

    except PyMongoError as e:
        logger.error(f"Failed to create TV show indexes: {str(e)}")
        raise



async def setup_indexes():
    """
    Set up indexes for both movie and TV show collections.
    Uses the singleton collection instances from the dependency system.
    """
    movies_collection = get_movies_collection()
    tv_collection = get_tv_collection()
    
    logger.info("Setting up movie collection indexes...")
    await _create_movie_indexes(movies_collection)
    
    logger.info("Setting up TV show collection indexes...")
    await _create_tv_indexes(tv_collection)

__all__ = ['setup_indexes']