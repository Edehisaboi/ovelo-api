import time
import asyncio
from config.settings import Settings

class TMDbRateLimiter:
    def __init__(self, settings: Settings):
        self.rate_limit = settings.TMDB_RATE_LIMIT
        self.rate_window = settings.TMDB_RATE_WINDOW
        self.requests: list[float] = []
        self.enabled = settings.ENABLE_RATE_LIMITING

    async def acquire(self) -> None:
        """Acquire a rate limit token, waiting if necessary."""
        if not self.enabled:
            return

        now = time.time()
        
        # Remove old requests outside the window
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < self.rate_window]
        
        # If we've hit the rate limit, wait until we can make another request
        if len(self.requests) >= self.rate_limit:
            sleep_time = self.requests[0] + self.rate_window - now
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            self.requests = self.requests[1:]
        
        # Add current request
        self.requests.append(now)

    def reset(self) -> None:
        """Reset the rate limiter state."""
        self.requests.clear() 