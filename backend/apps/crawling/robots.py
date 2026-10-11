from __future__ import annotations

import logging
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx

from apps.crawling.exceptions import RobotsDisallowedError

logger = logging.getLogger(__name__)

_ALLOW_ALL = ["User-agent: *", "Allow: /"]


class RobotsChecker:
    def __init__(self, user_agent: str, fetcher=None):
        self.user_agent = user_agent
        self._fetcher = fetcher
        self._parsers: dict[str, RobotFileParser] = {}

    def _parser(self, url: str) -> RobotFileParser:
        origin = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        if origin in self._parsers:
            return self._parsers[origin]
        robots_url = urljoin(origin + "/", "robots.txt")
        parser = RobotFileParser()
        parser.set_url(robots_url)
        body = self._load(robots_url)
        parser.parse((body or "\n".join(_ALLOW_ALL)).splitlines())
        self._parsers[origin] = parser
        return parser

    def _load(self, robots_url: str) -> str:
        try:
            if self._fetcher:
                return self._fetcher(robots_url)
            response = httpx.get(
                robots_url,
                headers={"User-Agent": self.user_agent},
                timeout=15.0,
                follow_redirects=True,
            )
        except httpx.HTTPError as exc:
            logger.info("robots.txt unavailable for %s (%s); allowing crawl", robots_url, exc)
            return "\n".join(_ALLOW_ALL)
        # urllib.robotparser.read() treats 403 as disallow-all. A blocked
        # default Python UA is not a robots rule, so only parse a real body.
        if response.status_code == 404 or response.status_code >= 400:
            logger.info(
                "robots.txt HTTP %s for %s; allowing crawl",
                response.status_code,
                robots_url,
            )
            return "\n".join(_ALLOW_ALL)
        return response.text

    def assert_allowed(self, url: str) -> None:
        parser = self._parser(url)
        if not parser.can_fetch(self.user_agent, url):
            raise RobotsDisallowedError(f"robots.txt disallows {url}")
