from unittest.mock import Mock

import pytest
from celery.exceptions import Retry

from apps.crawling.exceptions import CrawlerError
from apps.crawling.models import CrawlRun
from apps.news.models import Article
from apps.news.tasks import crawl_portal_news, fetch_article
from tests.conftest import fixture_text


@pytest.mark.django_db
def test_crawl_portal_news_fans_out(monkeypatch, eager_celery):
    html = fixture_text("merolagani", "article_page.html")
    listed = ["https://merolagani.com/NewsDetail.aspx?newsID=131653"]

    class FakeCrawler:
        def list_article_urls(self):
            return listed

        def fetch(self, url):
            return html

        def parse_article(self, page, url):
            return {
                "url": url,
                "portal": "merolagani",
                "title": "Locking period ends for six companies",
                "body": "body",
                "raw_date": "Oct 11, 2026 11:21 AM",
                "published_at": None,
            }

        def close(self):
            return None

    monkeypatch.setattr("apps.news.tasks.get_crawler", lambda portal: FakeCrawler())
    monkeypatch.setattr("apps.analysis.tasks.categorize_article.delay", Mock())
    created = crawl_portal_news("merolagani")
    assert created == 1
    assert Article.objects.filter(url=listed[0]).count() == 1
    run = CrawlRun.objects.filter(kind="news", portal="merolagani").latest("started_at")
    assert run.status == CrawlRun.Status.SUCCESS


@pytest.mark.django_db
def test_failed_crawl_writes_crawlrun(monkeypatch, eager_celery):
    class Boom:
        def list_article_urls(self):
            raise CrawlerError("portal down")

        def close(self):
            return None

    monkeypatch.setattr("apps.news.tasks.get_crawler", lambda portal: Boom())
    with pytest.raises(CrawlerError):
        crawl_portal_news("merolagani")
    run = CrawlRun.objects.filter(kind="news", portal="merolagani").latest("started_at")
    assert run.status == CrawlRun.Status.FAILED
    assert "portal down" in run.error


@pytest.mark.django_db
def test_fetch_article_failure_is_logged(monkeypatch, eager_celery):
    class Boom:
        def fetch(self, url):
            raise CrawlerError("bad url")

        def parse_article(self, html, url):
            return {}

        def close(self):
            return None

    monkeypatch.setattr("apps.news.tasks.get_crawler", lambda portal: Boom())
    with pytest.raises((CrawlerError, Retry)):
        fetch_article("merolagani", "https://merolagani.com/NewsDetail.aspx?newsID=0")
    run = CrawlRun.objects.filter(status=CrawlRun.Status.FAILED).latest("started_at")
    assert "bad url" in run.error
