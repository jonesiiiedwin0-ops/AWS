"""Token-bucket rate limiter."""

import threading
import time
from typing import Dict


class RateLimitExceeded(Exception):
    """Raised when a caller exceeds the configured rate limit."""

    def __init__(self, retry_after: float):
        super().__init__(f"Rate limit exceeded. Retry after {retry_after:.2f}s")
        self.retry_after = retry_after


class TokenBucket:
    """A single token bucket.

    Tokens refill continuously at ``rate`` per second up to ``capacity``.
    Each allowed request consumes one token.
    """

    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self._tokens = float(capacity)
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        self._last = now

    def acquire(self, tokens: int = 1) -> None:
        """Consume tokens or raise RateLimitExceeded.

        Raises:
            RateLimitExceeded: If insufficient tokens are available.
        """
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return
            deficit = tokens - self._tokens
            retry_after = deficit / self.rate if self.rate > 0 else float("inf")
            raise RateLimitExceeded(retry_after)

    @property
    def available(self) -> float:
        """Current number of available tokens (approximate)."""
        with self._lock:
            self._refill()
            return self._tokens


class RateLimiter:
    """Per-key rate limiter backed by token buckets.

    Keys are typically client identifiers (IP, API key). Each key gets its own
    bucket created lazily on first use.
    """

    def __init__(self, rate: float = 100.0, capacity: int = 200):
        """Initialize the rate limiter.

        Args:
            rate: Sustained requests per second allowed per key.
            capacity: Maximum burst size per key.
        """
        self.rate = rate
        self.capacity = capacity
        self._buckets: Dict[str, TokenBucket] = {}
        self._lock = threading.Lock()

    def check(self, key: str = "global", tokens: int = 1) -> None:
        """Check and consume rate-limit tokens for ``key``.

        Raises:
            RateLimitExceeded: If the key has exhausted its tokens.
        """
        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                bucket = TokenBucket(self.rate, self.capacity)
                self._buckets[key] = bucket
        bucket.acquire(tokens)

    def reset(self, key: str) -> None:
        """Remove a key's bucket, resetting its allowance."""
        with self._lock:
            self._buckets.pop(key, None)
