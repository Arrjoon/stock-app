import time
from unittest.mock import Mock

import fakeredis
import pytest

from apps.crawling.exceptions import RobotsDisallowedError
from apps.crawling.rate_limit import RedisRateLimiter
from apps.crawling.robots import RobotsChecker
from apps.crawling.urls import normalize_url
from apps.news.crawlers.merolagani import MeroLaganiCrawler


def test_normalize_url_strips_fragment_utm_and_slash():
    assert (
        normalize_url("https://www.sharesansar.com/newsdetail/gold/?utm_source=x#top")
        == "https://www.sharesansar.com/newsdetail/gold"
    )


def test_robots_disallow_raises_and_skips_http():
    http = Mock()
    checker = RobotsChecker(
        "StockAppBot/0.1",
        fetcher=lambda url: "User-agent: *\nDisallow: /api/\n",
    )
    crawler = MeroLaganiCrawler(client=http, robots=checker, rate_limiter=Mock(wait=Mock()))
    with pytest.raises(RobotsDisallowedError):
        crawler.fetch("https://nepsealpha.com/api/secret")
    http.get.assert_not_called()


def test_rate_limiter_spaces_calls():
    limiter = RedisRateLimiter(fakeredis.FakeRedis())
    start = time.monotonic()
    limiter.wait("merolagani", 0.2)
    limiter.wait("merolagani", 0.2)
    assert time.monotonic() - start >= 0.2
