"""Tests for the token-bucket rate limiter."""

import time

import pytest

from aws_mcp_server.rate_limiter import (
    RateLimiter,
    RateLimitExceeded,
    TokenBucket,
)


def test_bucket_allows_within_capacity():
    bucket = TokenBucket(rate=10, capacity=5)
    for _ in range(5):
        bucket.acquire()  # should not raise


def test_bucket_blocks_over_capacity():
    bucket = TokenBucket(rate=1, capacity=2)
    bucket.acquire()
    bucket.acquire()
    with pytest.raises(RateLimitExceeded) as exc:
        bucket.acquire()
    assert exc.value.retry_after > 0


def test_bucket_refills_over_time():
    bucket = TokenBucket(rate=100, capacity=1)
    bucket.acquire()
    time.sleep(0.05)  # ~5 tokens refilled
    bucket.acquire()  # should not raise


def test_rate_limiter_per_key_isolation():
    limiter = RateLimiter(rate=1, capacity=1)
    limiter.check("client-a")
    limiter.check("client-b")  # separate bucket, allowed
    with pytest.raises(RateLimitExceeded):
        limiter.check("client-a")  # client-a exhausted


def test_rate_limiter_reset():
    limiter = RateLimiter(rate=1, capacity=1)
    limiter.check("client-a")
    limiter.reset("client-a")
    limiter.check("client-a")  # allowed again after reset
