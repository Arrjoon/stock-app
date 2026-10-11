from datetime import datetime

from apps.news.models import Article
from apps.news.parsers import (
    extract_bizmandu_urls,
    extract_merolagani_urls,
    extract_sharesansar_urls,
    parse_bizmandu_article,
    parse_merolagani_article,
    parse_sharesansar_article,
)
from tests.conftest import fixture_text


def test_merolagani_parser():
    urls = extract_merolagani_urls(
        fixture_text("merolagani", "list_page.html"),
        "https://merolagani.com",
    )
    assert "https://merolagani.com/NewsDetail.aspx?newsID=131653" in urls
    parsed = parse_merolagani_article(
        fixture_text("merolagani", "article_page.html"),
        urls[0],
    )
    assert parsed["portal"] == "merolagani"
    assert "Locking period" in parsed["title"]
    assert "unlocked" in parsed["body"]
    assert parsed["url"].startswith("https://merolagani.com/NewsDetail.aspx")
    assert parsed["published_at"] is not None
    assert parsed["published_at"].year == 2026


def test_sharesansar_parser_prefers_slug_date():
    urls = extract_sharesansar_urls(
        fixture_text("sharesansar", "list_page.html"),
        "https://www.sharesansar.com",
    )
    article_url = [url for url in urls if "gold-price" in url][0]
    parsed = parse_sharesansar_article(
        fixture_text("sharesansar", "article_page.html"),
        article_url,
    )
    assert parsed["portal"] == "sharesansar"
    assert parsed["title"].startswith("Gold Price")
    assert "800" in parsed["body"]
    assert parsed["published_at"] is not None
    assert parsed["published_at"].year == 2026


def test_bizmandu_parser_mixed_date():
    urls = extract_bizmandu_urls(
        fixture_text("bizmandu", "list_page.html"),
        "https://wp.bizmandu.com",
    )
    assert urls == ["https://wp.bizmandu.com/content/20221214164554.html"]
    parsed = parse_bizmandu_article(
        fixture_text("bizmandu", "article_page.html"),
        urls[0],
    )
    assert parsed["portal"] == "bizmandu"
    assert "NEPSE" in parsed["title"]
    assert "freeze" in parsed["body"].lower() or "instructed" in parsed["body"]
    assert parsed["raw_date"]
    assert parsed["published_at"] is None or isinstance(parsed["published_at"], datetime)


def test_duplicate_url_creates_one_article(db):
    Article.objects.get_or_create(
        url="https://merolagani.com/NewsDetail.aspx?newsID=131653",
        defaults={"portal": "merolagani", "title": "one"},
    )
    Article.objects.get_or_create(
        url="https://merolagani.com/NewsDetail.aspx?newsID=131653",
        defaults={"portal": "merolagani", "title": "two"},
    )
    assert Article.objects.filter(url__contains="131653").count() == 1
