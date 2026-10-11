from __future__ import annotations

from apps.crawling.base import BaseCrawler
from apps.crawling.urls import normalize_url
from apps.news.parsers import (
    extract_sharesansar_cursor,
    extract_sharesansar_urls,
    parse_sharesansar_article,
)


class ShareSansarCrawler(BaseCrawler):
    portal = "sharesansar"

    def list_article_urls(self) -> list[str]:
        list_url = self.config["news_list_url"]
        max_pages = int(self.config.get("max_pages", 1))
        urls: list[str] = []
        cursor = ""
        for page in range(max_pages):
            if page == 0:
                url = list_url
            elif cursor:
                separator = "&" if "?" in list_url else "?"
                url = f"{list_url}{separator}cursor={cursor}"
            else:
                separator = "&" if "?" in list_url else "?"
                url = f"{list_url}{separator}page={page + 1}"
            html = self.fetch(url)
            batch = extract_sharesansar_urls(html, self.config["base_url"])
            new = [item for item in batch if item not in urls]
            if not new:
                break
            urls.extend(new)
            cursor = extract_sharesansar_cursor(html)
        return list(dict.fromkeys(normalize_url(url) for url in urls if url))

    def parse_article(self, html: str, url: str) -> dict:
        return parse_sharesansar_article(html, url)
