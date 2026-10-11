from __future__ import annotations

from apps.crawling.base import BaseCrawler
from apps.crawling.urls import normalize_url
from apps.news.parsers import extract_bizmandu_urls, parse_bizmandu_article


class BizmanduCrawler(BaseCrawler):
    portal = "bizmandu"

    def list_article_urls(self) -> list[str]:
        list_url = self.config["news_list_url"].rstrip("/")
        max_pages = int(self.config.get("max_pages", 1))
        urls: list[str] = []
        for page in range(1, max_pages + 1):
            url = list_url if page == 1 else f"{list_url}/page/{page}"
            html = self.fetch(url)
            batch = extract_bizmandu_urls(html, self.config["base_url"])
            new = [item for item in batch if item not in urls]
            if not new:
                break
            urls.extend(new)
        return list(dict.fromkeys(normalize_url(url) for url in urls if url))

    def parse_article(self, html: str, url: str) -> dict:
        return parse_bizmandu_article(html, url)
