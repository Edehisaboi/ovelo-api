import time
import asyncio
from typing import Optional, Any, Dict, List, Tuple
from config import get_logger, Settings
from api.services.database import tv_collection, movies_collection
from api.services.tmdb import TMDbClient
from motor.motor_asyncio import AsyncIOMotorClient
from api.services.database.db_query import search_movie_by_title, search_tv_by_title
from api.services.tmdb.models import SearchResults

logger = get_logger(__name__)


class SearchController:
    def __init__(
            self,
            tmdb_client:    TMDbClient,
    ):
        self.tmdb_client =          tmdb_client
        self.movies_collection =    movies_collection
        self.tv_collection =        tv_collection
        self.cache =                SearchCache()

    async def _search_database(
            self,
            query:          str,
            limit:          int = Settings.MAX_RESULTS_PER_PAGE,
            language:       Optional[str] = None,
            country:        Optional[str] = None,
            year:           Optional[int] = None,
            adult:          bool = True
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Search both movies and TV shows in the database."""
        try:
            # Search movies
            movies = await search_movie_by_title(
                self.movies_collection,
                query,
                exact_match=False,
                language=language,
                country=country,
                year=year,
                limit=limit//2
            )

            # Search TV shows
            tv_shows = await search_tv_by_title(
                self.tv_collection,
                query,
                exact_match=False,
                language=language,
                country=country,
                year=year,
                limit=limit//2
            )

            return movies, tv_shows

        except Exception as e:
            logger.error(f"Error searching database: {str(e)}")
            return [], []

    async def _search_tmdb(
            self,
            query:          str,
            limit:          int = Settings.MAX_RESULTS_PER_PAGE,
            language:       Optional[str] = None,
            country:        Optional[str] = None,
            year:           Optional[int] = None,
            adult:          bool = True
    ) -> Tuple[SearchResults, SearchResults]:
        """Search both movies and TV shows using TMDb API."""
        try:
            # Search both movies and TV shows in parallel
            movie_results, tv_results = await asyncio.gather(
                self.tmdb_client.search.movies(
                    query,
                    language=language or Settings.TMDB_LANGUAGE,
                    region=country or Settings.TMDB_REGION,
                    year=year,
                    include_adult=adult
                ),
                self.tmdb_client.search.tv_shows(
                    query,
                    language=language or Settings.TMDB_LANGUAGE,
                    include_adult=adult
                )
            )

            # Extract results
            movies = movie_results.results[:limit//2]
            tv_shows = tv_results.results[:limit//2]

            return movies, tv_shows

        except Exception as e:
            logger.error(f"Error searching TMDb: {str(e)}")
            return [], []

    async def search(
            self,
            query:          str,
            limit:          int = Settings.MAX_RESULTS_PER_PAGE,
            language:       Optional[str] = None,
            country:        Optional[str] = None,
            year:           Optional[int] = None,
            adult:          bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Main search method that searches both movies and TV shows.
        
        Args:
            query (str): The search query string
            limit (int, optional): Maximum number of results per type. Defaults to Settings.MAX_RESULTS_PER_PAGE.
            language (str, optional): Language code for results (e.g., 'en-US'). Defaults to None.
            country (str, optional): Country code for results (e.g., 'US'). Defaults to None.
            year (int, optional): Filter results by year. Defaults to None.
            adult (bool, optional): Include adult content. Defaults to True.
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Dictionary containing 'movies' and 'tv_shows' lists
        """
        # Create cache key including all search parameters
        cache_key = f"{query}:{limit}:{language}:{country}:{year}:{adult}"
        cached_results = self.cache.get(cache_key)
        if cached_results:
            return cached_results

        # Try database search first
        movies, tv_shows = await self._search_database(
            query,
            limit,
            language,
            country,
            year,
            adult
        )

        # If we don't have enough results, search TMDb
        if len(movies) < limit//2 or len(tv_shows) < limit//2:
            tmdb_movies, tmdb_tv_shows = await self._search_tmdb(
                query,
                limit,
                language,
                country,
                year,
                adult
            )
            
            # Combine results, ensuring no duplicates
            existing_movie_ids = {
                movie["tmdb_id"]
                for movie in movies
            }
            existing_tv_ids = {
                tv["tmdb_id"]
                for tv in tv_shows
            }
            
            # Add only new movies and TV shows
            movies.extend([
                movie for movie in tmdb_movies 
                if movie.id not in existing_movie_ids
            ])
            tv_shows.extend([
                tv for tv in tmdb_tv_shows 
                if tv.id not in existing_tv_ids
            ])

        # Prepare final results
        results = {
            "movies": movies[:limit//2],
            "tv_shows": tv_shows[:limit//2]
        }

        # Cache results if enabled
        if Settings.ENABLE_CACHING:
            self.cache.set(cache_key, results)

        return results

class SearchCache:
    def __init__(
            self
    ) -> None:
        self.ttl =          Settings.SEARCH_CACHE_TTL
        self.max_size =     Settings.SEARCH_CACHE_MAX_SIZE
        self.enabled =      Settings.ENABLE_CACHING
        self._cache:        Dict[str, tuple[float, Any]] = {}

    def _cleanup(
            self
    ) -> None:
        """Remove expired entries and enforce size limit."""
        now = time.time()
        
        # Remove expired entries
        self._cache = {
            key: (timestamp, value)
            for key, (timestamp, value) in self._cache.items()
            if now - timestamp < self.ttl
        }
        
        # Enforce size limit
        if len(self._cache) > self.max_size:
            # Sort by timestamp and keep only the newest entries
            sorted_items = sorted(
                self._cache.items(),
                key=lambda x: x[1][0],
                reverse=True
            )
            self._cache = dict(sorted_items[:self.max_size])

    def get(
            self,
            key:            str
    ) -> Optional[Any]:
        """
        Get a value from the cache if it exists and is not expired.
        
        Args:
            key (str): The cache key to retrieve
            
        Returns:
            Optional[Any]: The cached value if it exists and is not expired, None otherwise
        """
        if not self.enabled:
            return None
            
        if key not in self._cache:
            return None
            
        timestamp, value = self._cache[key]
        if time.time() - timestamp > self.ttl:
            del self._cache[key]
            return None
            
        return value

    def set(
            self,
            key:            str,
            value:          Any
    ) -> None:
        """
        Set a value in the cache with current timestamp.
        
        Args:
            key (str): The cache key to set
            value (Any): The value to cache
        """
        if not self.enabled:
            return
            
        self._cleanup()
        self._cache[key] = (time.time(), value)

    def clear(
            self
    ) -> None:
        """Clear all entries from the cache."""
        self._cache.clear()


class IngestionProcessor:
    def __init__(
        self,
        settings: Settings,
        db: AsyncIOMotorClient,
        embedding_service: EmbeddingService,
        tmdb_client: TMDbClient
    ):
        self.settings = settings
        self.db = db
        self.embedding_service = embedding_service
        self.tmdb_client = tmdb_client
        self.movies_collection = self.db[settings.MONGODB_DB][settings.MOVIES_COLLECTION]
        self.tv_collection = self.db[settings.MONGODB_DB][settings.TV_COLLECTION]

    async def process_movie(self, movie_data: SearchResult) -> Optional[Dict[str, Any]]:
        """Process a single movie for ingestion."""
        try:
            # Get full movie details from TMDb
            movie_details = await self.tmdb_client.movies.get_details(movie_data.id)
            if not movie_details:
                logger.warning(f"No details found for movie {movie_data.id}")
                return None

            # Create embedding for the movie
            overview = movie_details.overview
            if not overview:
                logger.warning(f"No overview found for movie {movie_data.id}")
                return None

            embedding = await self.embedding_service.get_embedding(overview)
            if not embedding:
                logger.error(f"Failed to create embedding for movie {movie_data.id}")
                return None

            # Prepare document for database
            document = {
                "tmdb_id": movie_details.id,
                "title": movie_details.title,
                "overview": overview,
                "poster_path": movie_details.poster_path,
                "release_date": movie_details.release_date,
                "vote_average": movie_details.vote_average,
                "embedding": embedding
            }

            # Upsert to database
            await self.movies_collection.update_one(
                {"tmdb_id": document["tmdb_id"]},
                {"$set": document},
                upsert=True
            )

            logger.info(f"Successfully processed movie {movie_data.id}")
            return document

        except Exception as e:
            logger.error(f"Error processing movie {movie_data.id}: {str(e)}")
            return None

    async def process_tv_show(self, tv_data: SearchResult) -> Optional[Dict[str, Any]]:
        """Process a single TV show for ingestion."""
        try:
            # Get full TV show details from TMDb
            tv_details = await self.tmdb_client.tv.get_details(tv_data.id)
            if not tv_details:
                logger.warning(f"No details found for TV show {tv_data.id}")
                return None

            # Create embedding for the TV show
            overview = tv_details.overview
            if not overview:
                logger.warning(f"No overview found for TV show {tv_data.id}")
                return None

            embedding = await self.embedding_service.get_embedding(overview)
            if not embedding:
                logger.error(f"Failed to create embedding for TV show {tv_data.id}")
                return None

            # Prepare document for database
            document = {
                "tmdb_id": tv_details.id,
                "name": tv_details.name,
                "overview": overview,
                "poster_path": tv_details.poster_path,
                "first_air_date": tv_details.first_air_date,
                "vote_average": tv_details.vote_average,
                "embedding": embedding
            }

            # Upsert to database
            await self.tv_collection.update_one(
                {"tmdb_id": document["tmdb_id"]},
                {"$set": document},
                upsert=True
            )

            logger.info(f"Successfully processed TV show {tv_data.id}")
            return document

        except Exception as e:
            logger.error(f"Error processing TV show {tv_data.id}: {str(e)}")
            return None

    async def process_results(
        self,
        movies: List[SearchResult],
        tv_shows: List[SearchResult]
    ) -> None:
        """Process search results asynchronously."""
        if not self.settings.INGESTION_ENABLED:
            logger.info("Ingestion is disabled, skipping processing")
            return

        tasks = []
        
        # Process movies
        for movie in movies:
            tasks.append(self.process_movie(movie))
            
        # Process TV shows
        for tv_show in tv_shows:
            tasks.append(self.process_tv_show(tv_show))
            
        # Wait for all tasks to complete and handle exceptions
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log any exceptions that occurred during processing
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error during ingestion: {str(result)}") 