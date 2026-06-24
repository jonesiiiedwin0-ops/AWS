"""Tests for the TTL cache."""

import time

from aws_mcp_server.cache import TTLCache


def test_set_and_get():
    cache = TTLCache(default_ttl=10)
    cache.set("k", {"v": 1})
    assert cache.get("k") == {"v": 1}


def test_expiry():
    cache = TTLCache(default_ttl=1)
    cache.set("k", "v", ttl=0)  # already expired
    time.sleep(0.01)
    assert cache.get("k") is None


def test_miss_returns_none():
    cache = TTLCache()
    assert cache.get("nope") is None


def test_invalidate():
    cache = TTLCache()
    cache.set("k", "v")
    assert cache.invalidate("k") is True
    assert cache.invalidate("k") is False


def test_max_size_eviction():
    cache = TTLCache(default_ttl=100, max_size=2)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)  # forces eviction
    assert cache.stats()["size"] == 2


def test_stats_tracks_hits_and_misses():
    cache = TTLCache()
    cache.set("k", "v")
    cache.get("k")  # hit
    cache.get("x")  # miss
    stats = cache.stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert 0 < stats["hit_rate"] <= 1
