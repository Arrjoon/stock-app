from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import httpx
from django.conf import settings
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from apps.crawling.exceptions import PortalDisabledError
from apps.crawling.rate_limit import RedisRateLimiter
from apps.crawling.robots import RobotsChecker
from apps.crawling.urls import normalize_url

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    portal: str = ""

    def __init__(self, client=None, rate_limiter=None, robots=None):
        self.config = settings.CRAWLER_CONFIG[self.portal]
        if not self.config.get("enabled", True):
            raise PortalDisabledError(f"{self.portal} is disabled")
        self.user_agent = settings.CRAWLER_USER_AGENT
        self.timeout = settings.CRAWLER_TIMEOUT
        self.client = client or httpx.Client(
            headers={"User-Agent": self.user_agent, "Accept-Language": "en,ne;q=0.8"},
            timeout=self.timeout,
            follow_redirects=True,
        )
        self.owns_client = client is None
        self.rate_limiter = rate_limiter or RedisRateLimiter()
        self.robots = robots or RobotsChecker(self.user_agent)

    def close(self):
        if self.owns_client:
            self.client.close()

    def fetch(self, url: str) -> str:
        url = normalize_url(url)
        self.robots.assert_allowed(url)
        self.rate_limiter.wait(self.portal, float(self.config.get("min_interval", 1)))
        return self._get(url)

    @retry(
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        wait=wait_exponential(multiplier=1, min=1, max=20),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def _get(self, url: str) -> str:
        logger.info("GET %s", url)
        response = self.client.get(url)
        if response.status_code in {429, 500, 502, 503, 504}:
            response.raise_for_status()
        response.raise_for_status()
        return response.text

    @abstractmethod
    def list_article_urls(self) -> list[str]:
        """Return normalized article URLs from the portal listing."""

    @abstractmethod
    def parse_article(self, html: str, url: str) -> dict:
        """Pure HTML parse. Must not perform network I/O."""
