import httpx

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from application.utils.rate_limiter import RateLimiter


class BaseAPIClient(ABC):
    """Base interface for all API clients."""
    
    @abstractmethod
    async def get(
        self,
        endpoint:   str,
        params:     Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a GET request to the API."""
        pass
    
    @abstractmethod
    async def post(
        self,
        endpoint:   str,
        json_body:  Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make a POST request to the API."""
        pass


class AbstractAPIClient(BaseAPIClient):
    """Abstract base class implementing common API client functionality."""
    def __init__(
        self,
        api_key:        str,
        http_client:    httpx.AsyncClient,
        base_url:       str,
        rate_limiter:   'RateLimiter'
    ) -> None:
        self.http_client   = http_client
        self._api_key      = api_key
        self._base_url     = base_url.rstrip('/')
        self._rate_limiter = rate_limiter
        
    async def get(
        self,
        endpoint:   str,
        params:     Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a GET request to the API with rate limiting."""
        await self._rate_limiter.acquire()
        params = params or {}
        
        response = await self.http_client.get(
            f"{self._base_url}/{endpoint.lstrip('/')}",
            params=params,
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    async def post(
        self,
        endpoint:   str,
        json_body:  Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make a POST request to the API with rate limiting."""
        await self._rate_limiter.acquire()
        
        response = await self.http_client.post(
            f"{self._base_url}/{endpoint.lstrip('/')}",
            json=json_body,
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    @abstractmethod
    def _get_headers(self) -> Dict[str, str]:
        """Get the headers for API requests."""
        pass 