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

        # Retry loop: compute under lock; if we must sleep, do it outside the lock
        while True:
            async with self._lock:
                now = time.time()

                # Remove timestamps that are outside the rate window
                while self._requests and now - self._requests[0] >= self._config.rate_window:
                    self._requests.popleft()

                # If there's capacity, record and return
                if len(self._requests) < self._config.rate_limit:
                    self._requests.append(now)
                    return

                # Compute sleep time until next slot frees up
                sleep_time = self._requests[0] + self._config.rate_window - now

            # Sleep outside the lock to avoid deadlocks/starvation
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            else:
                # Yield control briefly before retrying
                await asyncio.sleep(0)

    def reset(self) -> None:
        """Reset the rate limiter state (clears all request timestamps)."""
        self._requests.clear()
