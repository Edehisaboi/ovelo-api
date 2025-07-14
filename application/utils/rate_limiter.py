import time
import asyncio
from dataclasses import dataclass
from collections import deque

@dataclass
class RateLimitConfig:
    rate_limit: int           # Max requests allowed in the window
    rate_window: int          # Time window in seconds
    enabled: bool = True      # Toggle rate limiting on/off

class RateLimiter:
    def __init__(self, config: RateLimitConfig):
        self._config = config
        self._requests = deque()          # Holds timestamps of recent requests
        self._lock = asyncio.Lock()       # Ensures safe concurrent access

    async def acquire(self) -> None:
        """Acquire a rate limit token, waiting if necessary."""
        if not self._config.enabled:
            return

        async with self._lock:
            now = time.time()

            # Remove timestamps that are outside the rate window
            while self._requests and now - self._requests[0] >= self._config.rate_window:
                self._requests.popleft()

            # If at rate limit, wait until a slot is available
            if len(self._requests) >= self._config.rate_limit:
                sleep_time = self._requests[0] + self._config.rate_window - now
                if sleep_time > 0:
                    self._lock.release()          # Release lock while sleeping
                    try:
                        await asyncio.sleep(sleep_time)
                    finally:
                        await self._lock.acquire()
                    now = time.time()
                    # Remove anymore expired requests after waking
                    while self._requests and now - self._requests[0] >= self._config.rate_window:
                        self._requests.popleft()

            # Record the timestamp of this request
            self._requests.append(time.time())

    def reset(self) -> None:
        """Reset the rate limiter state (clears all request timestamps)."""
        self._requests.clear()
