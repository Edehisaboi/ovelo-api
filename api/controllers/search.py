import time
import asyncio
from typing import Optional, Any, Dict, List, Tuple
from functools import lru_cache

from api.clients import TMDbClient
from api.services.embedding import EmbeddingService
from config import get_logger, Settings
from api.services.database import tv_collection, movies_collection, media_document
from api.services.database.db_query import search_movie_by_title, search_tv_by_title
from api.services.tmdb.model import SearchResults, SearchResult
from api.services.subtitle import opensubtitles_client, subtitle_processor

logger = get_logger(__name__)


class SearchController:
    def __init__(
        self,
        tmdb_client: TMDbClient,
        settings: Settings
    ):
        self.movies_collection     = movies_collection
        self.tv_collection         = tv_collection
        self.tmdb_client           = tmdb_client
        self.settings              = settings
        self.cache                 = SearchCache(settings=settings)

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
        return f"{query.lower()}:{limit}:{language}:{country}:{year}:{adult}"

    async def _search_database(
        self,
        query: str,
        limit: int = None,
        language: Optional[str] = None,
        country: Optional[str] = None,
        year: Optional[int] = None,
        adult: bool = True
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        try:
            limit = limit or self.settings.MAX_RESULTS_PER_PAGE
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
        query: str,
        limit: int = None,
        language: Optional[str] = None,
        country: Optional[str] = None,
        year: Optional[int] = None,
        adult: bool = True
    ) -> Tuple[SearchResults, SearchResults]:
        try:
            limit = limit or self.settings.MAX_RESULTS_PER_PAGE
            movie_results, tv_results = await asyncio.gather(
                self.tmdb_client.search.movies(
                    query,
                    language=language or self.settings.TMDB_LANGUAGE,
                    region=country or self.settings.TMDB_REGION,
                    year=year,
                    include_adult=adult
                ),
                self.tmdb_client.search.tv_shows(
                    query,
                    language=language or self.settings.TMDB_LANGUAGE,
                    include_adult=adult
                )
            )

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
        existing_movie_ids = {movie["tmdb_id"] for movie in local_movies}
        existing_tv_ids    = {tv["tmdb_id"] for tv in local_tv}

        new_movies = [movie for movie in tmdb_movies if movie.id not in existing_movie_ids]
        new_tv     = [tv for tv in tmdb_tv if tv.id not in existing_tv_ids]

        return local_movies + new_movies, local_tv + new_tv

    async def search(
        self,
        query: str,
        limit: int = None,
        language: Optional[str] = None,
        country: Optional[str] = None,
        year: Optional[int] = None,
        adult: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        limit = limit or self.settings.MAX_RESULTS_PER_PAGE

        cache_key = self._generate_cache_key(query, limit, language, country, year, adult)
        cached_results = self.cache.get(cache_key)
        if cached_results:
            return cached_results

        local_movies, local_tv = await self._search_database(query, limit, language, country, year, adult)

        if len(local_movies) < limit//2 or len(local_tv) < limit//2:
            tmdb_movies, tmdb_tv = await self._search_tmdb(query, limit, language, country, year, adult)
            movies, tv_shows = self._deduplicate_results(local_movies, local_tv, tmdb_movies, tmdb_tv)
        else:
            movies, tv_shows = local_movies, local_tv

        results = {
            "movies": movies[:limit//2],
            "tv_shows": tv_shows[:limit//2]
        }

        if self.settings.ENABLE_CACHING:
            self.cache.set(cache_key, results)

        return results
    

class SearchCache:
    def __init__(
        self,
        settings: Settings
    ) -> None:
        self.settings  = settings
        self.ttl       = settings.SEARCH_CACHE_TTL
        self.max_size  = settings.SEARCH_CACHE_MAX_SIZE
        self.enabled   = settings.ENABLE_CACHING
        self._cache: Dict[str, Tuple[float, Any]] = {}

    def _cleanup(self) -> None:
        """Remove expired entries and enforce size limit."""
        now = time.time()
        self._cache = {
            key: (timestamp, value)
            for key, (timestamp, value) in self._cache.items()
            if now - timestamp < self.ttl
        }

        if len(self._cache) > self.max_size:
            sorted_items = sorted(
                self._cache.items(),
                key=lambda x: x[1][0],  # sort by timestamp
                reverse=True
            )
            self._cache = dict(sorted_items[:self.max_size])

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a cached value if present and not expired."""
        if not self.enabled or key not in self._cache:
            return None

        timestamp, value = self._cache[key]
        if time.time() - timestamp > self.ttl:
            del self._cache[key]
            return None

        return value

    def set(self, key: str, value: Any) -> None:
        """Set a new cache entry."""
        if not self.enabled:
            return

        self._cleanup()
        self._cache[key] = (time.time(), value)

    def clear(self) -> None:
        """Clear the entire cache."""
        self._cache.clear()



class IngestionProcessor:
    def __init__(
        self,
        settings: Settings,
        embedding_service: EmbeddingService,
        tmdb_client: TMDbClient
    ):
        self.settings           = settings
        self.embedding_service = embedding_service
        self.tmdb_client        = tmdb_client
        self.movies_collection  = movies_collection
        self.tv_collection      = tv_collection

    async def process_movie(self, movie_data: SearchResult) -> Optional[Dict[str, Any]]:
        try:
            movie_details = await self.tmdb_client.movies.details(movie_data.id)
            if not movie_details:
                logger.warning(f"No details found for movie {movie_data.id}")
                return None

            subtitles = await opensubtitles_client.search.by_tmdb(
                tmdb_id=movie_details.id,
                language=self.settings.OPEN_SUBTITLES_LANGUAGE,
                order_by=self.settings.OPEN_SUBTITLES_ORDER_BY,
                order_direction=self.settings.OPEN_SUBTITLES_ORDER_DIRECTION,
                trusted_sources=self.settings.OPEN_SUBTITLES_TRUSTED_SOURCES
            )

            if not subtitles or not subtitles[0].attributes.files:
                logger.warning(f"No subtitles found for TMDB ID {movie_details.id}")
                return None

            subtitle_file = await opensubtitles_client.subtitles.download(
                subtitle_file=subtitles[0].attributes.files[0]
            )

            subtitle_chunks = subtitle_processor.process(
                srt_content=subtitle_file.subtitle_text
            )

            embeddings = await self.embedding_service.update_with_embeddings(
                transcript_chunks=subtitle_chunks
            )

            movie_details.model_copy(update={
                "transcript_chunks": embeddings,
                "embedding_model": self.settings.EMBEDDING_MODEL
            })

            movie_document = media_document.movie_document(movie=movie_details)

            await self.movies_collection.update_one(
                {"tmdb_id": movie_details.id},
                {"$set": movie_document},
                upsert=True
            )

            logger.info(f"Successfully processed movie {movie_data.id}")
            return movie_document

        except Exception as e:
            logger.error(f"Error processing movie {movie_data.id}: {str(e)}")
            return None

    async def process_tv_show(self, tv_data: SearchResult) -> Optional[Dict[str, Any]]:
        try:
            logger.info(f"TV ingestion not implemented for {tv_data.id}")
            raise NotImplementedError("TV ingestion is not yet implemented.")
        except Exception as e:
            logger.error(f"Error processing TV show {tv_data.id}: {str(e)}")
            return None

    async def process_results(
        self,
        movies: List[SearchResult],
        tv_shows: List[SearchResult]
    ) -> None:
        if not self.settings.INGESTION_ENABLED:
            logger.info("Ingestion is disabled, skipping processing")
            return

        tasks = [
            self.process_movie(movie) for movie in movies
        ] + [
            self.process_tv_show(tv_show) for tv_show in tv_shows
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error during ingestion task {i}: {str(result)}")
