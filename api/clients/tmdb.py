import httpx
import asyncio
from typing import Dict, Any, Optional, List
from .base import AbstractAPIClient
from api.services.rate_limiting.limiter import RateLimiter
from api.services.tmdb.model import (
    MovieDetails, MovieCredits, MovieImages, MovieVideos,
    TVDetails, WatchProviders, SearchResults, Season
)

class TMDbClient(AbstractAPIClient):
    """TMDb API client implementation."""
    
    def __init__(
        self,
        api_key:        str,
        http_client:    httpx.AsyncClient,
        base_url:       str,
        rate_limiter:   Optional[RateLimiter] = None
    ) -> None:
        super().__init__(api_key, http_client, base_url, rate_limiter)
        
        # Initialize API sections
        self._search = SearchService(self)
        self._movies = MoviesService(self)
        self._tv = TVService(self)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get the headers for TMDb API requests."""
        return {
            "accept":       "application/json",
            "Authorization": f"Bearer {self._api_key}"
        }
    
    @property
    def search(self) -> 'SearchService':
        """Get the search service."""
        return self._search
    
    @property
    def movies(self) -> 'MoviesService':
        """Get the movies service."""
        return self._movies
    
    @property
    def tv(self) -> 'TVService':
        """Get the TV service."""
        return self._tv

class SearchService:
    """TMDb search service implementation."""
    
    def __init__(self, client: TMDbClient) -> None:
        self._client = client
    
    async def multi(
        self,
        query:          str,
        page:           int = 1,
        language: str = "en-US",
        include_adult:  bool = True,
        region:         Optional[str] = None,
        year:           Optional[int] = None
    ) -> SearchResults:
        """Search for movies, TV shows, and people."""
        params = {
            "query":        query,
            "page":         page,
            "language":     language,
            "include_adult":include_adult
        }
        if region:
            params["region"] = region
        if year:
            params["year"] = year
            
        data = await self._client.get("/search/multi", params)
        return SearchResults(**data)
    
    async def movies(
        self,
        query:          str,
        page:           int = 1,
        language:       str = "en-US",
        include_adult:  bool = True,
        region:         Optional[str] = None,
        year:           Optional[int] = None
    ) -> SearchResults:
        """Search for movies."""
        params = {
            "query":        query,
            "page":         page,
            "language":     language,
            "include_adult": include_adult
        }
        if region:
            params["region"] = region
        if year:
            params["year"] = year
            
        data = await self._client.get("/search/movie", params)
        return SearchResults(**data)
    
    async def tv_shows(
        self,
        query:          str,
        page:           int = 1,
        language:       str = "en-US",
        include_adult:  bool = True
    ) -> SearchResults:
        """Search for TV shows."""
        params = {
            "query":        query,
            "page":         page,
            "language":     language,
            "include_adult": include_adult
        }
        
        data = await self._client.get("/search/tv", params)
        return SearchResults(**data)

class MoviesService:
    """TMDb movies service implementation."""
    
    def __init__(self, client: TMDbClient) -> None:
        self._client = client
    
    async def details(
        self,
        movie_id:           int,
        params:             Optional[Dict[str, Any]] = None,
        append_to_response: Optional[str] = "credits,images,external_ids,videos,watch/providers"
    ) -> MovieDetails:
        """Get movie details."""
        params = params or {}
        if append_to_response:
            params["append_to_response"] = append_to_response
            
        data = await self._client.get(f"/movie/{movie_id}", params)
        return MovieDetails(**data)
    
    async def credits(self, movie_id: int) -> MovieCredits:
        """Get movie credits."""
        data = await self._client.get(f"/movie/{movie_id}/credits")
        return MovieCredits(**data)
    
    async def images(
        self,
        movie_id:   int,
        params:     Optional[Dict[str, Any]] = None
    ) -> MovieImages:
        """Get movie images."""
        data = await self._client.get(f"/movie/{movie_id}/images", params)
        return MovieImages(**data)
    
    async def videos(
            self,
            movie_id: int
    ) -> MovieVideos:
        """Get movie videos."""
        data = await self._client.get(f"/movie/{movie_id}/videos")
        return MovieVideos(**data)
    
    async def watch_providers(
        self,
        movie_id: int
    ) -> WatchProviders:
        """Get movie watch providers."""
        data = await self._client.get(f"/movie/{movie_id}/watch/providers")
        return WatchProviders(**data)

class TVService:
    """TMDb TV service implementation."""
    
    def __init__(self, client: TMDbClient) -> None:
        self._client = client
    
    async def season_details(
        self,
        tv_id:          int,
        season_number:  int,
        params:         Optional[Dict[str, Any]] = None
    ) -> Season:
        """Get TV season details."""
        data = await self._client.get(f"/tv/{tv_id}/season/{season_number}", params)
        return Season(**data)
    
    async def get_all_seasons_with_episodes(
        self,
        tv_id:              int,
        number_of_seasons:  int
    ) -> List[Season]:
        """Get all seasons with episodes for a TV show."""
        tasks = [
            self.season_details(tv_id, season_num)
            for season_num in range(1, number_of_seasons + 1)
        ]
        return await asyncio.gather(*tasks)
    
    async def details(
        self,
        tv_id:              int,
        params:             Optional[Dict[str, Any]] = None,
        append_to_response: Optional[str] = "credits,images,external_ids,videos,watch/providers",
        include_seasons:    bool = True
    ) -> TVDetails:
        """Get TV show details."""
        params = params or {}
        if append_to_response:
            params["append_to_response"] = append_to_response
            
        # Get basic TV details
        data = await self._client.get(f"/tv/{tv_id}", params)
        
        # If seasons are requested, fetch them in parallel
        if include_seasons:
            seasons_data = await self.get_all_seasons_with_episodes(
                tv_id, 
                data["number_of_seasons"]
            )
            data["seasons"] = seasons_data
            
        return TVDetails(**data)
    
    async def credits(
        self,
        tv_id: int
    ) -> MovieCredits:
        """Get TV show credits."""
        data = await self._client.get(f"/tv/{tv_id}/credits")
        return MovieCredits(**data)
    
    async def images(
        self,
        tv_id: int,
        params: Optional[Dict[str, Any]] = None
    ) -> MovieImages:
        """Get TV show images."""
        data = await self._client.get(f"/tv/{tv_id}/images", params)
        return MovieImages(**data)
    
    async def videos(
        self,
        tv_id: int
        ) -> MovieVideos:
        """Get TV show videos."""
        data = await self._client.get(f"/tv/{tv_id}/videos")
        return MovieVideos(**data)
    
    async def watch_providers(
        self,
        tv_id: int
    ) -> WatchProviders:
        """Get TV show watch providers."""
        data = await self._client.get(f"/tv/{tv_id}/watch/providers")
        return WatchProviders(**data)
    