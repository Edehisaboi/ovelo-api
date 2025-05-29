import time
import asyncio
from typing import Optional, Any, Dict, List, Tuple
from functools import lru_cache

from api.services.embedding import EmbeddingService
from config import get_logger, Settings
from api.services.database import tv_collection, movies_collection, media_document
from api.services.tmdb import TMDbClient
from api.services.database.db_query import search_movie_by_title, search_tv_by_title
from api.services.tmdb.model import SearchResults, SearchResult
from api.services.subtitle import opensubtitles_client, subtitle_chunker

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

    @lru_cache(maxsize=1000)
    def _generate_cache_key(
            self,
            query: str,
            limit: int,
            language: Optional[str],
            country: Optional[str],
            year: Optional[int],
            adult: bool
    ) -> str:
        """Generate a consistent cache key for search parameters."""
        return f"{query.lower()}:{limit}:{language}:{country}:{year}:{adult}"

    async def _search_database(
            self,
            query:          str,
            limit:          int = Settings.MAX_RESULTS_PER_PAGE,
            language:       Optional[str] = None,
            country:        Optional[str] = None,
            year:           Optional[int] = None,
            adult:          bool = True
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Search both movies and TV shows in the database in parallel."""
        try:
            # Search movies and TV shows concurrently
            movies, tv_shows = await asyncio.gather(
                search_movie_by_title(
                    self.movies_collection,
                    query,
                    exact_match=False,
                    language=language,
                    country=country,
                    year=year,
                    limit=limit//2
                ),
                search_tv_by_title(
                    self.tv_collection,
                    query,
                    exact_match=False,
                    language=language,
                    country=country,
                    year=year,
                    limit=limit//2
                )
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
        """Search both movies and TV shows using TMDb API in parallel."""
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
            movies = movie_results.results[:limit//2] if movie_results and movie_results.results else []
            tv_shows = tv_results.results[:limit//2] if tv_results and tv_results.results else []

            return movies, tv_shows

        except Exception as e:
            logger.error(f"Error searching TMDb: {str(e)}")
            return [], []

    def _deduplicate_results(
            self,
            local_movies: List[Dict[str, Any]],
            local_tv: List[Dict[str, Any]],
            tmdb_movies: List[SearchResult],
            tmdb_tv: List[SearchResult]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Deduplicate and merge results from local DB and TMDb."""
        # Create sets of existing IDs
        existing_movie_ids = {movie["tmdb_id"] for movie in local_movies}
        existing_tv_ids = {tv["tmdb_id"] for tv in local_tv}
        
        # Add only new movies and TV shows
        new_movies = [
            movie for movie in tmdb_movies 
            if movie.id not in existing_movie_ids
        ]
        new_tv = [
            tv for tv in tmdb_tv 
            if tv.id not in existing_tv_ids
        ]
        
        return local_movies + new_movies, local_tv + new_tv

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
        # Generate cache key
        cache_key = self._generate_cache_key(query, limit, language, country, year, adult)
        cached_results = self.cache.get(cache_key)
        if cached_results:
            return cached_results

        # First search local database
        local_movies, local_tv = await self._search_database(
            query, limit, language, country, year, adult
        )

        # Only search TMDb if we don't have enough results
        if len(local_movies) < limit//2 or len(local_tv) < limit//2:
            tmdb_movies, tmdb_tv = await self._search_tmdb(
                query, limit, language, country, year, adult
            )
            
            # Deduplicate and merge results
            movies, tv_shows = self._deduplicate_results(
                local_movies, local_tv,
                tmdb_movies, tmdb_tv
            )
        else:
            movies, tv_shows = local_movies, local_tv

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
        """Get a value from the cache if it exists and is not expired."""
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
        """Set a value in the cache with current timestamp."""
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
        embedding_service: EmbeddingService,
        tmdb_client: TMDbClient
    ):
        self.settings = settings
        self.embedding_service = embedding_service
        self.tmdb_client = tmdb_client
        self.movies_collection = movies_collection
        self.tv_collection = tv_collection

    async def process_movie(self, movie_data: SearchResult) -> Optional[Dict[str, Any]]:
        """Process a single movie for ingestion."""
        try:
            # Get full movie details from TMDb
            movie_details = await self.tmdb_client.movies.details(movie_data.id)
            if not movie_details:
                logger.warning(f"No details found for movie {movie_data.id}")
                return None

            # Search for the movie subtitle
            subtitles = await opensubtitles_client.search.by_tmdb(
                tmdb_id=movie_details.id,
                language=Settings.OPEN_SUBTITLES_LANGUAGE,
                order_by=Settings.OPEN_SUBTITLES_ORDER_BY,
                order_direction=Settings.OPEN_SUBTITLES_ORDER_DIRECTION,
                trusted_sources=Settings.OPEN_SUBTITLES_TRUSTED_SOURCES,
            )

            # Download the movie subtitle
            subtitle_file = await opensubtitles_client.subtitles.download(
                subtitle_file=subtitles[0].attributes.files[0]
            )

            # Parse and chunk the movie subtitle
            subtitle_chunks = subtitle_chunker.chunk_subtitle(
                srt_content=subtitle_file.subtitle_text
            )

            # Create embedding for the movie
            embeddings = await self.embedding_service.update_with_embeddings(
                transcript_chunks=subtitle_chunks
            )

            # update the movie details with the embedding
            movie_details.model_copy(
                update={
                    "transcript_chunks": embeddings,
                    "embedding_model": Settings.EMBEDDING_MODEL
                }
            )

            # Prepare document for database
            movie_document = media_document.movie_document(
                movie=movie_details,
            )

            # Upsert to database
            await self.movies_collection.update_one(
                {"$set": movie_document},
                upsert=True
            )

            logger.info(f"Successfully processed movie {movie_data.id}")
            return movie_document

        except Exception as e:
            logger.error(f"Error processing movie {movie_data.id}: {str(e)}")
            return None

    async def process_tv_show(self, tv_data: SearchResult) -> Optional[Dict[str, Any]]:
        pass

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
                