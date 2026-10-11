from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from apps.crawling.dates import parse_published_at
from apps.crawling.urls import normalize_url

_NEWS_ID = re.compile(r"NewsDetail\.aspx\?newsID=\d+", re.I)
_SHARESANSAR = re.compile(r"/newsdetail/[A-Za-z0-9\-]+", re.I)
_BIZMANDU = re.compile(r"/content/\d[\w-]*\.html", re.I)
_SLUG_DATE = re.compile(r"(\d{4}-\d{2}-\d{2})$")
_SKIP_BIZ = ("/category/", "/feed", "advertise", "member-login", "/reporter/")


def _text(node) -> str:
    if not node:
        return ""
    return " ".join(node.get_text(" ", strip=True).split())


def _meta(soup: BeautifulSoup, *keys: str) -> str:
    for key in keys:
        tag = soup.find("meta", property=key) or soup.find("meta", attrs={"name": key})
        if tag and tag.get("content"):
            return tag["content"].strip()
    return ""


def extract_merolagani_urls(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    found: list[str] = []
    seen: set[str] = set()
    for anchor in soup.select('a[href*="NewsDetail.aspx"]'):
        href = anchor.get("href") or ""
        if not _NEWS_ID.search(href):
            continue
        url = normalize_url(urljoin(base_url.rstrip("/") + "/", href))
        if url and url not in seen:
            seen.add(url)
            found.append(url)
    return found


def parse_merolagani_article(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    title = _meta(soup, "og:title") or _text(soup.select_one("h4.newsTitle"))
    body = _text(soup.select_one("#ctl00_ContentPlaceHolder1_newsOverview")) or _text(
        soup.select_one("div.media-content")
    )
    raw_date = _text(soup.select_one("#ctl00_ContentPlaceHolder1_newsDate")) or _text(
        soup.select_one("span.media-label")
    )
    published_at = parse_published_at(raw_date)
    return {
        "url": normalize_url(url),
        "portal": "merolagani",
        "title": title,
        "body": body,
        "raw_date": raw_date,
        "published_at": published_at,
    }


def extract_sharesansar_urls(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    found: list[str] = []
    seen: set[str] = set()
    for anchor in soup.select('a[href*="/newsdetail/"]'):
        href = anchor.get("href") or ""
        if not _SHARESANSAR.search(href):
            continue
        url = normalize_url(urljoin(base_url.rstrip("/") + "/", href))
        if url and url not in seen:
            seen.add(url)
            found.append(url)
    return found


def extract_sharesansar_cursor(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    node = soup.find(attrs={"data-next-cursor": True}) or soup.find(id="next_cursor")
    if node:
        return (node.get("data-next-cursor") or node.get("value") or "").strip()
    match = re.search(r'"next_cursor"\s*:\s*"([^"]+)"', html)
    return match.group(1) if match else ""


def parse_sharesansar_article(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    title = _meta(soup, "og:title") or _text(soup.select_one("div.detail h1"))
    body = _text(soup.select_one("#newsdetail-content"))
    slug_date = ""
    match = _SLUG_DATE.search(urlparse_path(url))
    if match:
        slug_date = match.group(1)
    visible = _text(soup.select_one("div.detail i.date")) or _text(soup.select_one("i.date"))
    meta_date = _meta(soup, "article:published_time")
    raw_date = slug_date or visible or meta_date
    published_at = parse_published_at(slug_date or visible) or parse_published_at(meta_date)
    return {
        "url": normalize_url(url),
        "portal": "sharesansar",
        "title": title,
        "body": body,
        "raw_date": raw_date,
        "published_at": published_at,
    }


def urlparse_path(url: str) -> str:
    from urllib.parse import urlparse

    return urlparse(url).path


def extract_bizmandu_urls(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    found: list[str] = []
    seen: set[str] = set()
    for anchor in soup.select('a[href*="/content/"]'):
        href = anchor.get("href") or ""
        if not _BIZMANDU.search(href):
            continue
        if any(skip in href for skip in _SKIP_BIZ):
            continue
        url = normalize_url(urljoin(base_url.rstrip("/") + "/", href))
        if url and url not in seen:
            seen.add(url)
            found.append(url)
    return found


def parse_bizmandu_article(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    title = _meta(soup, "og:title") or _text(soup.select_one("h1.detail_title"))
    if title.endswith(" - BIZMANDU"):
        title = title[: -len(" - BIZMANDU")].strip()
    body = _text(soup.select_one("div.biz-article-content div.news-text")) or _text(
        soup.select_one("div.news-text")
    )
    raw_date = _text(soup.select_one("div.author span")) or _meta(soup, "article:published_time")
    calendar = soup.select_one("div.right-icon span")
    if calendar:
        raw_date = _text(calendar)
    published_at = parse_published_at(raw_date)
    return {
        "url": normalize_url(url),
        "portal": "bizmandu",
        "title": title,
        "body": body,
        "raw_date": raw_date,
        "published_at": published_at,
    }
