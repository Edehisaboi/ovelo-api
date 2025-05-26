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
    ) -> None:
        self.http_client = http_client
        self.api_key =  api_key
        self.base_url = base_url.rstrip('/')
        
        # Initialize API sections
        self.search =   SearchAPI(self)
        self.movies =   MoviesAPI(self)
        self.tv =       TVAPI(self)

    async def get(
        self,
        endpoint:       str,
        params:         Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        params = params or {}
        params["api_key"] = self.api_key

        response = await self.http_client.get(
            f"{self.base_url}/{endpoint.lstrip('/')}",
            params=params
        )
        response.raise_for_status()
        return response.json()

class SearchAPI:
    def __init__(self, client: TMDbClient) -> None:
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
        params = {
            "query":         query,
            "page":          page,
            "language":      language,
            "include_adult": include_adult
        }
        if region:
            params["region"] = region
        if year:
            params["year"] = year

        data = await self.client.get("/search/multi", params)
        return SearchResults(**data)

    async def movies(
        self,
        query:          str,
        page:           int = 1,
        language:       str = "en-US",
        include_adult:  bool = False,
        region:         Optional[str] = None,
        year:           Optional[int] = None
    ) -> SearchResults:
        params = {
            "query":         query,
            "page":          page,
            "language":      language,
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
        include_adult:      bool = False
    ) -> SearchResults:
        params = {
            "query":              query,
            "page":               page,
            "language":           language,
            "include_adult":      include_adult
        }

        data = await self.client.get("/search/tv", params)
        return SearchResults(**data)

class MoviesAPI:
    def __init__(self, client: TMDbClient) -> None:
        self.client = client

    async def details(
        self,
        movie_id:           int,
        params:             Optional[Dict[str, Any]] = None,
        append_to_response: Optional[str] = "credits,images,external_ids,videos,watch/providers"
    ) -> MovieDetails:
        params = params or {}
        if append_to_response:
            params["append_to_response"] = append_to_response
        data = await self.client.get(f"/movie/{movie_id}", params)
        return MovieDetails(**data)

    async def credits(
        self,
        movie_id:           int
    ) -> MovieCredits:
        data = await self.client.get(f"/movie/{movie_id}/credits")
        return MovieCredits(**data)

    async def images(
        self,
        movie_id:           int,
        params:             Optional[Dict[str, Any]] = None
    ) -> MovieImages:
        data = await self.client.get(f"/movie/{movie_id}/images", params)
        return MovieImages(**data)

    async def videos(
        self,
        movie_id:           int
    ) -> MovieVideos:
        data = await self.client.get(f"/movie/{movie_id}/videos")
        return MovieVideos(**data)

    async def watch_providers(
        self,
        movie_id:           int
    ) -> WatchProviders:
        data = await self.client.get(f"/movie/{movie_id}/watch/providers")
        return WatchProviders(**data)

class TVAPI:
    def __init__(self, client: TMDbClient) -> None:
        self.client = client

    async def season_details(
        self,
        tv_id:              int,
        season_number:      int,
        params:             Optional[Dict[str, Any]] = None
    ) -> Season:
        data = await self.client.get(f"/tv/{tv_id}/season/{season_number}", params)
        return Season(**data)

    async def get_all_seasons_with_episodes(
        self,
        tv_id:              int,
        number_of_seasons:  int
    ) -> List[Season]:
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
        data = await self.client.get(f"/tv/{tv_id}/credits")
        return MovieCredits(**data)

    async def images(
        self,
        tv_id:              int,
        params:             Optional[Dict[str, Any]] = None
    ) -> MovieImages:
        data = await self.client.get(f"/tv/{tv_id}/images", params)
        return MovieImages(**data)

    async def videos(
        self,
        tv_id:              int
    ) -> MovieVideos:
        data = await self.client.get(f"/tv/{tv_id}/videos")
        return MovieVideos(**data)

    async def watch_providers(
        self,
        tv_id:              int
    ) -> WatchProviders:
        data = await self.client.get(f"/tv/{tv_id}/watch/providers")
        return WatchProviders(**data)
