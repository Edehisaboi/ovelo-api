import time
import asyncio
from dataclasses import dataclass
from config import Settings

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    rate_limit: int
    rate_window: int
    enabled: bool = True

class RateLimiter:
    """Generic rate limiter implementation."""
    
    def __init__(self, config: RateLimitConfig):
        self._config = config
        self._requests: list[float] = []
    
    async def acquire(self) -> None:
        """Acquire a rate limit token, waiting if necessary."""
        if not self._config.enabled:
            return
            
        now = time.time()
        
        # Remove old requests outside the window
        self._requests = [
            req_time for req_time in self._requests 
            if now - req_time < self._config.rate_window
        ]
        
        # If we've hit the rate limit, wait until we can make another request
        if len(self._requests) >= self._config.rate_limit:
            sleep_time = self._requests[0] + self._config.rate_window - now
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            self._requests = self._requests[1:]
        
        # Add current request
        self._requests.append(now)
    
    def reset(self) -> None:
        """Reset the rate limiter state."""
        self._requests.clear()
    
    @classmethod
    def from_settings(cls, settings: Settings, service: str) -> 'RateLimiter':
        """Create a rate limiter from settings."""
        config = RateLimitConfig(
            rate_limit=getattr(settings, f"{service.upper()}_RATE_LIMIT"),
            rate_window=getattr(settings, f"{service.upper()}_RATE_WINDOW"),
            enabled=settings.ENABLE_RATE_LIMITING
        )
        return cls(config) 