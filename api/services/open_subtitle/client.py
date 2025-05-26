import httpx
from typing import Optional, Dict, Any, List
from .models import SubtitleSearchResults, SubtitleFile
from .rate_limiter import OpenSubtitlesRateLimiter
from config import Settings

class OpenSubtitlesClient:
    def __init__(
        self,
        api_key: str,
        http_client: httpx.AsyncClient,
        base_url: str,
        settings: Settings
    ) -> None:
        self.http_client = http_client
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.rate_limiter = OpenSubtitlesRateLimiter(settings)

        # Initialize API sections
        self.search = SearchAPI(self)
        self.subtitles = SubtitlesAPI(self)

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a GET request to the OpenSubtitles API with rate limiting."""
        await self.rate_limiter.acquire()
        params = params or {}

        response = await self.http_client.get(
            f"{self.base_url}/{endpoint.lstrip('/')}",
            params=params,
            headers={
                "User-Agent":   "Moovzmatch/1.0",
                "Api-Key":      self.api_key
            }
        )
        response.raise_for_status()
        return response.json()

    async def post(
        self,
        endpoint: str,
        json_body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make a POST request to the OpenSubtitles API with rate limiting."""
        await self.rate_limiter.acquire()

        response = await self.http_client.post(
            f"{self.base_url}/{endpoint.lstrip('/')}",
            json=json_body,
            headers={
                "User-Agent":   "Moovzmatch/1.0",
                "Api-Key":      self.api_key,
                "Content-Type": "application/json",
                "Accept":       "application/json"
            }
        )
        response.raise_for_status()
        return response.json()


class SearchAPI:
    def __init__(self, client: OpenSubtitlesClient) -> None:
        self.client = client

    async def _build_params(
        self,
        id_key: str,
        id_value: str | int,
        language: str,
        season_number: Optional[int],
        episode_number: Optional[int],
        order_by: Optional[str],
        order_direction: Optional[str],
        trusted_sources: Optional[bool] = None
    ) -> Dict[str, Any]:
        params = {
            id_key: id_value,
            "languages": language
        }
        if season_number:
            params["season_number"] = season_number
        if episode_number:
            params["episode_number"] = episode_number
        if order_by:
            params["order_by"] = order_by
        if order_direction:
            params["order_direction"] = order_direction
        if trusted_sources is not None:
            params["trusted_sources"] = str(trusted_sources).lower()
        return params

    async def by_imdb(
        self,
        imdb_id: str,
        language: str = "en",
        season_number: Optional[int] = None,
        episode_number: Optional[int] = None,
        order_by: Optional[List[str]] = None,
        order_direction: Optional[str] = None,
        trusted_sources: Optional[bool] = None
    ) -> SubtitleSearchResults:
        """Search subtitles by IMDb ID. Use parent_imdb_id for TV shows."""
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
        data = await self.client.get("/subtitles", params)
        return SubtitleSearchResults(**data)

    async def by_tmdb(
        self,
        tmdb_id: int,
        language: str = "en",
        season_number: Optional[int] = None,
        episode_number: Optional[int] = None,
        order_by: Optional[List[str]] = None,
        order_direction: Optional[str] = None,
        trusted_sources: Optional[bool] = None
    ) -> SubtitleSearchResults:
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
        data = await self.client.get("/subtitles", params)
        return SubtitleSearchResults(**data)

    async def by_parent(
        self,
        parent_type: str,  # 'imdb' or 'tmdb'
        parent_id: str | int,
        language: str = "en",
        season_number: Optional[int] = None,
        episode_number: Optional[int] = None,
        order_by: Optional[List[str]] = None,
        order_direction: Optional[str] = None,
        trusted_sources: Optional[bool] = None
    ) -> SubtitleSearchResults:
        """Search subtitles by parent_imdb_id or parent_tmdb_id for TV shows."""
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
        data = await self.client.get("/subtitles", params)
        return SubtitleSearchResults(**data)


class SubtitlesAPI:
    def __init__(self, client: OpenSubtitlesClient) -> None:
        self.client = client

    async def download(
        self,
        subtitle_file: SubtitleFile
    ) -> SubtitleFile:
        """
        Download a subtitle file and return its content along with metadata.
        The subtitle text will be stored in the subtitle_text field of SubtitleFile.
        """
        data = await self.client.post(f"/download/", {"file_id": subtitle_file.file_id})

        download_url = data["link"]
        subtitle_text = await self.fetch_subtitle_text(download_url)

        return subtitle_file.model_copy(
            update={
                "download_url": download_url,
                "subtitle_text": subtitle_text
            }
        )

    async def fetch_subtitle_text(
        self,
        download_url: str
    ) -> str:
        """
        Fetch the subtitle text from the download URL.
        """
        response = await self.client.http_client.get(download_url)
        response.raise_for_status()
        return response.text
