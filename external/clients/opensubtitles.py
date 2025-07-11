import asyncio
from typing import Any, Dict, List, Optional

import httpx

from .base import AbstractAPIClient
from application.core.config import settings
from application.utils.rate_limiter import RateLimiter
from application.models import SubtitleFile, SubtitleSearchResult, SubtitleSearchResults, Season


class OpenSubtitlesClient(AbstractAPIClient):
    """OpenSubtitles API client implementation."""
    
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
        self._subtitles = SubtitlesService(self)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get the headers for OpenSubtitles API requests."""
        return {
            "User-Agent":   "Moovzmatch/1.0",
            "Content-Type": "application/json",
            "Accept":       "application/json",
            "Api-Key":      self._api_key,
        }
    
    @property
    def search(self) -> 'SearchService':
        """Get the search service."""
        return self._search
    
    @property
    def subtitles(self) -> 'SubtitlesService':
        """Get the subtitle service."""
        return self._subtitles

class SearchService:
    """OpenSubtitles search service implementation."""
    
    def __init__(self, client: OpenSubtitlesClient) -> None:
        self._client = client
    
    @staticmethod
    async def _build_params(
            id_key:          str,
            id_value:        str | int,
            season_number:   Optional[int] = None,
            episode_number:  Optional[int] = None,
            order_by:        Optional[str] = settings.OPENSUBTITLES_ORDER_BY,
            order_direction: Optional[str] = settings.OPENSUBTITLES_ORDER_DIRECTION,
            language:        str = settings.OPENSUBTITLES_LANGUAGE,
            trusted_sources: Optional[bool] = settings.OPENSUBTITLES_TRUSTED_SOURCES
    ) -> Dict[str, Any]:
        """
        Build and return params dict for OpenSubtitles API, keeping languages first.
        """
        params = {
            "languages": language,
            id_key : id_value
        }

        # Add other optional params if present
        if season_number is not None:
            params["season_number"] = season_number
        if episode_number is not None:
            params["episode_number"] = episode_number
        if order_by:
            params["order_by"] = order_by
        if order_direction:
            params["order_direction"] = order_direction
        if trusted_sources is not None:
            # OpenSubtitles expects 'true'/'false' as string, not bool
            params["trusted_sources"] = str(trusted_sources).lower()
        return params
    
    async def by_imdb(
        self,
        imdb_id:            str,
        language:           str = "en",
        season_number:      Optional[int] = None,
        episode_number:     Optional[int] = None,
        order_by:           Optional[str] = None,
        order_direction:    Optional[str] = None,
        trusted_sources:    Optional[bool] = None
    ) -> SubtitleSearchResults:
        """Search subtitles by IMDb ID."""
        params = await self._build_params(
            id_key="imdb_id",
            id_value=imdb_id.strip().lower(),
            language=language,
            season_number=season_number,
            episode_number=episode_number,
            order_by=order_by,
            order_direction=order_direction,
            trusted_sources=trusted_sources
        )
        data = await self._client.get("/subtitles", params)
        return SubtitleSearchResults(**data)
    
    async def by_tmdb(
        self,
        tmdb_id:           int,
        language:          str = "en",
        season_number:     Optional[int] = None,
        episode_number:    Optional[int] = None,
        order_by:          Optional[str] = None,
        order_direction:   Optional[str] = None,
        trusted_sources:   Optional[bool] = None
    ) -> Optional[SubtitleSearchResult]:
        """Search subtitles by TMDb ID."""
        params = await self._build_params(
            id_key="tmdb_id",
            id_value=tmdb_id,
            language=language,
            season_number=season_number,
            episode_number=episode_number,
            order_by=order_by,
            order_direction=order_direction,
            trusted_sources=trusted_sources
        )
        data = await self._client.get("/subtitles", params)
        search_results =  SubtitleSearchResults(**data)
        if search_results.results:
            return search_results.results[0]
        return None  # No subtitles found

    async def by_parent(
            self,
            parent_type:     str,
            parent_id:       str | int,
            language:        str = "en",
            season_number:   Optional[int] = None,
            episode_number:  Optional[int] = None,
            order_by:        Optional[str] = None,
            order_direction: Optional[str] = None,
            trusted_sources: Optional[bool] = None
    ) -> Optional[SubtitleSearchResult]:
        """Search subtitles by parent ID (for TV shows)"""
        param_key = f"parent_{parent_type.lower()}_id"
        params = await self._build_params(
            id_key=param_key,
            id_value=parent_id,
            language=language,
            season_number=season_number,
            episode_number=episode_number,
            order_by=order_by,
            order_direction=order_direction,
            trusted_sources=trusted_sources
        )
        data = await self._client.get("/subtitles", params)
        search_results = SubtitleSearchResults(**data)
        if search_results.results:
            return search_results.results[0]  # Return only the first/best result
        return None  # No subtitles found

    async def all_parent_search(
            self,
            parent_type: str,
            parent_id:   str | int,
            seasons:     List[Season]
    ) -> List[Optional[SubtitleSearchResult]]:
        """Search all subtitles for a parent (TV show) across all seasons and episodes, one best result per episode."""
        if not seasons:
            raise ValueError("Seasons list cannot be empty.")

        tasks = []
        for season in seasons:
            for episode_num in range(1, season.episode_count + 1):
                tasks.append(
                    self.by_parent(
                        parent_type=parent_type,
                        parent_id=parent_id,
                        season_number=season.season_number,
                        episode_number=episode_num
                    )
                )

        return await asyncio.gather(*tasks)


class SubtitlesService:
    """OpenSubtitles subtitles service implementation."""
    
    def __init__(self, client: OpenSubtitlesClient) -> None:
        self._client = client
    
    async def download(
        self,
        subtitle_file: SubtitleFile
    ) -> SubtitleFile:
        """Download a subtitle file."""
        if not subtitle_file or not subtitle_file.file_id:
            raise ValueError("Invalid subtitle file provided for download.")

        data = await self._client.post("/download", {"file_id": subtitle_file.file_id})
        
        download_url = data["link"]
        if not download_url:
            raise RuntimeError(f"Download link missing in response: {data}")

        subtitle_text = await self._fetch_subtitle_text(download_url)
        
        return subtitle_file.model_copy(
            update={
                "download_url": download_url,
                "subtitle_text": subtitle_text
            }
        )
    
    async def _fetch_subtitle_text(
        self,
        download_url: str
    ) -> str:
        """Fetch the subtitle text from the download URL."""
        response = await self._client.http_client.get(download_url)
        response.raise_for_status()
        return response.text 