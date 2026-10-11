from __future__ import annotations

import logging

from apps.crawling.base import BaseCrawler
from apps.crawling.browser import render_merolagani_list_pages
from apps.crawling.urls import normalize_url
from apps.news.parsers import extract_merolagani_urls, parse_merolagani_article

logger = logging.getLogger(__name__)


class MeroLaganiCrawler(BaseCrawler):
    portal = "merolagani"

    def list_article_urls(self) -> list[str]:
        list_url = self.config["news_list_url"]
        urls = extract_merolagani_urls(self.fetch(list_url), self.config["base_url"])
        extra_pages = int(self.config.get("max_pages", 1))
        if extra_pages > 1 and self.config.get("use_selenium"):
            try:
                snapshots = render_merolagani_list_pages(
                    list_url,
                    extra_pages,
                    self.user_agent,
                    self.timeout,
                )
                for html in snapshots:
                    urls.extend(extract_merolagani_urls(html, self.config["base_url"]))
            except Exception as exc:  # noqa: BLE001
                logger.warning("MeroLagani browser pagination failed: %s", exc)
        return list(dict.fromkeys(normalize_url(url) for url in urls if url))

    def parse_article(self, html: str, url: str) -> dict:
        return parse_merolagani_article(html, url)
