"""In-memory TTL cache for AWS responses."""

import threading
import time
from typing import Any, Dict, Optional, Tuple


class TTLCache:
    """A thread-safe in-memory cache with per-entry time-to-live.

    Designed for caching read-only AWS responses (e.g. list operations) to
    reduce API calls and latency. Not a replacement for a distributed cache;
    intended for single-instance deployments or as an L1 cache.
    """

    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        """Initialize the cache.

        Args:
            default_ttl: Default time-to-live in seconds for entries.
            max_size: Maximum number of entries before evicting the oldest.
        """
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._store: Dict[str, Tuple[float, Any]] = {}
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Return the cached value for ``key`` or ``None`` if missing/expired."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None
            expires_at, value = entry
            if time.monotonic() >= expires_at:
                del self._store[key]
                self._misses += 1
                return None
            self._hits += 1
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store ``value`` under ``key`` with an optional TTL override."""
        with self._lock:
            if len(self._store) >= self.max_size and key not in self._store:
                # Evict the entry closest to expiry.
                oldest = min(self._store, key=lambda k: self._store[k][0])
                del self._store[oldest]
            effective_ttl = ttl if ttl is not None else self.default_ttl
            expires_at = time.monotonic() + effective_ttl
            self._store[key] = (expires_at, value)

    def invalidate(self, key: str) -> bool:
        """Remove a single key. Returns True if it existed."""
        with self._lock:
            return self._store.pop(key, None) is not None

    def clear(self) -> None:
        """Remove all entries."""
        with self._lock:
            self._store.clear()

    def stats(self) -> Dict[str, Any]:
        """Return cache statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total) if total else 0.0
            return {
                "size": len(self._store),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 4),
            }
