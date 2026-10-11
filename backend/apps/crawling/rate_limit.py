from __future__ import annotations

import time

from django.conf import settings


class RedisRateLimiter:
    """One request per min_interval seconds per portal, across all workers."""

    def __init__(self, redis_client=None):
        self._redis = redis_client

    @property
    def redis(self):
        if self._redis is None:
            import redis

            self._redis = redis.Redis.from_url(settings.REDIS_URL)
        return self._redis

    def wait(self, portal: str, min_interval: float) -> None:
        if min_interval <= 0:
            return
        key = f"crawler:rate:{portal}"
        ttl_ms = max(int(min_interval * 1000), 1)
        while True:
            if self.redis.set(key, "1", nx=True, px=ttl_ms):
                return
            ttl = self.redis.pttl(key)
            sleep_for = (ttl / 1000) if ttl and ttl > 0 else 0.05
            time.sleep(min(sleep_for, min_interval))
