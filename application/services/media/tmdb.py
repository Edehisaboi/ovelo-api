from typing import Optional

from external.clients import TMDbClient
from application.models.media import SearchResults, MovieDetails, TVDetails
from application.core.logging import get_logger

logger = get_logger(__name__)


class TMDbService:
    """Service for TMDb API operations."""

    def __init__(self, client: TMDbClient):
        self.client = client

    async def search_movies(
        self,
        query:          str,
        page:           int = 1,
        language:       str = "en-US",
        include_adult:  bool = True,
        region:         Optional[str] = None,
        year:           Optional[int] = None
    ) -> SearchResults:
        """Search for movies using TMDb API."""
        try:
            results = await self.client.search.movies(
                query=query,
                page=page,
                language=language,
                include_adult=include_adult,
                region=region,
                year=year
            )
            return results
        except Exception as e:
            logger.error(f"Error searching movies: {e}")
            raise

    async def search_tv_shows(
        self,
        query:          str,
        page:           int = 1,
        language:       str = "en-US",
        include_adult:  bool = True
    ) -> SearchResults:
        """Search for TV shows using TMDb API."""
        try:
            results = await self.client.search.tv_shows(
                query=query,
                page=page,
                language=language,
                include_adult=include_adult
            )
            return results
        except Exception as e:
            logger.error(f"Error searching TV shows: {e}")
            raise

    async def search_multi(
        self,
        query:          str,
        page:           int = 1,
        language:       str = "en-US",
        include_adult:  bool = True,
        region:         Optional[str] = None,
        year:           Optional[int] = None
    ) -> SearchResults:
        """Search for movies, TV shows, and people using TMDb API."""
        try:
            results = await self.client.search.multi(
                query=query,
                page=page,
                language=language,
                include_adult=include_adult,
                region=region,
                year=year
            )
            return results
        except Exception as e:
            logger.error(f"Error performing multi-search: {e}")
            raise

    async def get_movie_details(
        self,
        movie_id: int
    ) -> MovieDetails:
        """Get detailed movie information from TMDb API."""
        try:
            details = await self.client.movies.details(movie_id)
            return details
        except Exception as e:
            logger.error(f"Error getting movie details: {e}")
            raise

    async def get_tv_details(
        self,
        tv_id: int,
        include_seasons: bool = True
    ) -> TVDetails:
        """Get detailed TV show information from TMDb API."""
        try:
            details = await self.client.tv.details(
                tv_id=tv_id,
                include_seasons=include_seasons
            )
            return details
        except Exception as e:
            logger.error(f"Error getting TV details: {e}")
            raise

    async def get_movie_credits(self, movie_id: int):
        """Get movie credits from TMDb API."""
        try:
            credits = await self.client.movies.credits(movie_id)
            return credits
        except Exception as e:
            logger.error(f"Error getting movie credits: {e}")
            raise

    async def get_tv_credits(self, tv_id: int):
        """Get TV show credits from TMDb API."""
        try:
            credits = await self.client.tv.credits(tv_id)
            return credits
        except Exception as e:
            logger.error(f"Error getting TV credits: {e}")
            raise

    async def get_movie_images(self, movie_id: int):
        """Get movie images from TMDb API."""
        try:
            images = await self.client.movies.images(movie_id)
            return images
        except Exception as e:
            logger.error(f"Error getting movie images: {e}")
            raise

    async def get_tv_images(self, tv_id: int):
        """Get TV show images from TMDb API."""
        try:
            images = await self.client.tv.images(tv_id)
            return images
        except Exception as e:
            logger.error(f"Error getting TV images: {e}")
            raise

    async def get_movie_videos(self, movie_id: int):
        """Get movie videos from TMDb API."""
        try:
            videos = await self.client.movies.videos(movie_id)
            return videos
        except Exception as e:
            logger.error(f"Error getting movie videos: {e}")
            raise

    async def get_tv_videos(self, tv_id: int):
        """Get TV show videos from TMDb API."""
        try:
            videos = await self.client.tv.videos(tv_id)
            return videos
        except Exception as e:
            logger.error(f"Error getting TV videos: {e}")
            raise

    async def get_movie_watch_providers(self, movie_id: int):
        """Get movie watch providers from TMDb API."""
        try:
            providers = await self.client.movies.watch_providers(movie_id)
            return providers
        except Exception as e:
            logger.error(f"Error getting movie watch providers: {e}")
            raise

    async def get_tv_watch_providers(self, tv_id: int):
        """Get TV show watch providers from TMDb API."""
        try:
            providers = await self.client.tv.watch_providers(tv_id)
            return providers
        except Exception as e:
            logger.error(f"Error getting TV watch providers: {e}")
            raise 