import httpx
from typing import Optional, Dict, Any, List
import asyncio
from .models import (
    MovieDetails, MovieCredits, MovieImages, MovieVideos,
    TVDetails, WatchProviders, SearchResults,
    Season,
)


class TMDbClient:
    def __init__(
        self,
        api_key:        str,
        http_client:    httpx.AsyncClient,
        base_url:       str
    ):
        self.http_client =  http_client
        self.api_key =      api_key
        self.base_url =     base_url.rstrip('/')
        
        # Initialize API sections
        self.search =   SearchAPI(self)
        self.movies =   MoviesAPI(self)
        self.tv =       TVAPI(self)

    async def get(
        self,
        endpoint:       str,
        params:         Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a GET request to the TMDB API.
        
        Args:
            endpoint (str): API endpoint to call
            params (dict, optional): Query parameters
            
        Returns:
            dict: JSON response from the API
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
        params = params or {}
        params["api_key"] = self.api_key

        response = await self.http_client.get(
            f"{self.base_url}/{endpoint.lstrip('/')}",
            params=params
        )
        response.raise_for_status()
        return response.json()

class SearchAPI:
    def __init__(self, client: TMDbClient):
        self.client = client

    async def multi(
        self,
        query:          str,
        page:           int = 1,
        language:       str = "en-US",
        include_adult:  bool = False,
        region:         Optional[str] = None,
        year:           Optional[int] = None
    ) -> SearchResults:
        """
        Search for movies and TV shows in a single request.
        
        Args:
            query (str): Search query
            page (int, optional): Page number. Defaults to 1.
            language (str, optional): Language code. Defaults to "en-US".
            include_adult (bool, optional): Include adult content. Defaults to False.
            region (str, optional): Region code for filtering results.
            year (int, optional): Filter by year.
            
        Returns:
            SearchResults: Search results containing both movies and TV shows
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
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

        data = await self.client.get("/search/multi", params)
        return SearchResults(**data)

    async def movies(
        self,
        query:              str,
        page:               int = 1,
        language:           str = "en-US",
        include_adult:      bool = False,
        region:             Optional[str] = None,
        year:               Optional[int] = None
    ) -> SearchResults:
        """
        Search for movies only.
        
        Args:
            query (str): Search query
            page (int, optional): Page number. Defaults to 1.
            language (str, optional): Language code. Defaults to "en-US".
            include_adult (bool, optional): Include adult content. Defaults to False.
            region (str, optional): Region code for filtering results.
            year (int, optional): Filter by year.
            
        Returns:
            SearchResults: Search results containing only movies
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
        params = {
            "query": query,
            "page": page,
            "language": language,
            "include_adult": include_adult
        }
        if region:
            params["region"] = region
        if year:
            params["year"] = year

        data = await self.client.get("/search/movie", params)
        return SearchResults(**data)

    async def tv_shows(
        self,
        query:              str,
        page:               int = 1,
        language:           str = "en-US",
        include_adult:      bool = False,
        first_air_date_year: Optional[int] = None
    ) -> SearchResults:
        """
        Search for TV shows only.
        
        Args:
            query (str): Search query
            page (int, optional): Page number. Defaults to 1.
            language (str, optional): Language code. Defaults to "en-US".
            include_adult (bool, optional): Include adult content. Defaults to False.
            first_air_date_year (int, optional): Filter by first air date year.
            
        Returns:
            SearchResults: Search results containing only TV shows
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
        params = {
            "query": query,
            "page": page,
            "language": language,
            "include_adult": include_adult
        }
        if first_air_date_year:
            params["first_air_date_year"] = first_air_date_year

        data = await self.client.get("/search/tv", params)
        return SearchResults(**data)

class MoviesAPI:
    def __init__(self, client: TMDbClient):
        self.client = client

    async def details(
        self,
        movie_id:           int,
        params:             Optional[Dict[str, Any]] = None,
        append_to_response: Optional[str] = "credits,images,external_ids,videos,watch/providers"
    ) -> MovieDetails:
        """
        Get movie details by ID with optional appended data.
        
        Args:
            movie_id (int): TMDB movie ID
            params (dict, optional): Additional parameters
            append_to_response (str, optional): Comma separated list of additional data to append
                e.g. "credits,images,videos". Maximum of 20 items can be appended.
                
        Returns:
            MovieDetails: 
                - Returns a MovieDetails model
                
        Raises:
            httpx.HTTPError: If the API request fails
        """
        params = params or {}
        if append_to_response:
            params["append_to_response"] = append_to_response
        data = await self.client.get(f"/movie/{movie_id}", params)
        return MovieDetails(**data)

    async def credits(
        self,
        movie_id:           int
    ) -> MovieCredits:
        """
        Get cast and crew credits for a movie.
        
        Args:
            movie_id (int): TMDB movie ID
            
        Returns:
            MovieCredits: Movie credits
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
        data = await self.client.get(f"/movie/{movie_id}/credits")
        return MovieCredits(**data)

    async def images(
        self,
        movie_id:           int,
        params:             Optional[Dict[str, Any]] = None
    ) -> MovieImages:
        """
        Get images (posters, backdrops, etc.) for a movie.
        
        Args:
            movie_id (int): TMDB movie ID
            params (dict, optional): Additional parameters
            
        Returns:
            MovieImages: Movie images
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
        data = await self.client.get(f"/movie/{movie_id}/images", params)
        return MovieImages(**data)

    async def videos(
        self,
        movie_id:           int
    ) -> MovieVideos:
        """
        Get videos (trailers, teasers, etc.) for a movie.
        
        Args:
            movie_id (int): TMDB movie ID
            
        Returns:
            MovieVideos: Movie videos
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
        data = await self.client.get(f"/movie/{movie_id}/videos")
        return MovieVideos(**data)

    async def watch_providers(
        self,
        movie_id:           int
    ) -> WatchProviders:
        """
        Get watch providers (streaming services) for a movie.
        
        Args:
            movie_id (int): TMDB movie ID
            
        Returns:
            WatchProviders: Movie watch providers
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
        data = await self.client.get(f"/movie/{movie_id}/watch/providers")
        return WatchProviders(**data)

class TVAPI:
    def __init__(self, client: TMDbClient):
        self.client = client

    async def season_details(
        self,
        tv_id: int,
        season_number: int,
        params: Optional[Dict[str, Any]] = None
    ) -> Season:
        """
        Get details for a specific season including episodes.
        
        Args:
            tv_id (int): TMDB TV show ID
            season_number (int): Season number
            params (dict, optional): Additional parameters
            
        Returns:
            Season: Season details with episodes
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
        data = await self.client.get(f"/tv/{tv_id}/season/{season_number}", params)
        return Season(**data)

    async def get_all_seasons_with_episodes(
        self,
        tv_id: int,
        number_of_seasons: int
    ) -> List[Season]:
        """
        Get all seasons with their episodes in parallel.
        
        Args:
            tv_id (int): TMDB TV show ID
            number_of_seasons (int): Total number of seasons
            
        Returns:
            List[Season]: List of seasons with their episodes
            
        Raises:
            httpx.HTTPError: If any API request fails
        """
        tasks = [
            self.season_details(tv_id, season_num)
            for season_num in range(1, number_of_seasons + 1)
        ]
        return await asyncio.gather(*tasks)

    async def details(
        self,
        tv_id: int,
        params: Optional[Dict[str, Any]] = None,
        append_to_response: Optional[str] = "credits,images,external_ids,videos,watch/providers",
        include_seasons: bool = True
    ) -> TVDetails:
        """
        Get TV show details by ID with optional appended data and season episodes.
        
        Args:
            tv_id (int): TMDB TV show ID
            params (dict, optional): Additional parameters
            append_to_response (str, optional): Comma separated list of additional data to append
            include_seasons (bool, optional): Whether to include full season data with episodes
            
        Returns:
            TVDetails: TV show details with optional season data
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
        params = params or {}
        if append_to_response:
            params["append_to_response"] = append_to_response
            
        # Get basic TV details
        data = await self.client.get(f"/tv/{tv_id}", params)
        
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
        tv_id:              int
    ) -> MovieCredits:
        """
        Get cast and crew credits for a TV show.
        
        Args:
            tv_id (int): TMDB TV show ID
            
        Returns:
            MovieCredits: TV show credits
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
        data = await self.client.get(f"/tv/{tv_id}/credits")
        return MovieCredits(**data)

    async def images(
        self,
        tv_id:              int,
        params:             Optional[Dict[str, Any]] = None
    ) -> MovieImages:
        """
        Get images (posters, backdrops, etc.) for a TV show.
        
        Args:
            tv_id (int): TMDB TV show ID
            params (dict, optional): Additional parameters
            
        Returns:
            MovieImages: TV show images
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
        data = await self.client.get(f"/tv/{tv_id}/images", params)
        return MovieImages(**data)

    async def videos(
        self,
        tv_id:              int
    ) -> MovieVideos:
        """
        Get videos (trailers, teasers, etc.) for a TV show.
        
        Args:
            tv_id (int): TMDB TV show ID
            
        Returns:
            MovieVideos: TV show videos
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
        data = await self.client.get(f"/tv/{tv_id}/videos")
        return MovieVideos(**data)

    async def watch_providers(
        self,
        tv_id:              int
    ) -> WatchProviders:
        """
        Get watch providers (streaming services) for a TV show.
        
        Args:
            tv_id (int): TMDB TV show ID
            
        Returns:
            WatchProviders: TV show watch providers
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
        data = await self.client.get(f"/tv/{tv_id}/watch/providers")
        return WatchProviders(**data)
