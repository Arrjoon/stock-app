from __future__ import annotations

import logging

from celery import shared_task
from django.conf import settings

from apps.crawling.exceptions import CrawlerError, PortalDisabledError
from apps.crawling.runs import finish_failed, finish_success, start_run
from apps.crawling.urls import normalize_url
from apps.news.crawlers import get_crawler
from apps.news.models import Article

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="apps.news.tasks.crawl_portal_news")
def crawl_portal_news(self, portal: str, run_id=None) -> int:
    run = start_run("news", portal=portal, run_id=run_id, task_id=self.request.id or "")
    crawler = None
    try:
        if not settings.CRAWLER_CONFIG.get(portal, {}).get("enabled", False):
            raise PortalDisabledError(f"{portal} is disabled")
        crawler = get_crawler(portal)
        urls = [normalize_url(url) for url in crawler.list_article_urls()]
        existing = set(Article.objects.filter(url__in=urls).values_list("url", flat=True))
        new_urls = [url for url in urls if url and url not in existing]
        for url in new_urls:
            fetch_article.delay(portal, url)
        finish_success(run, items=len(new_urls))
        return len(new_urls)
    except Exception as exc:  # noqa: BLE001
        finish_failed(run, str(exc))
        raise
    finally:
        if crawler is not None:
            crawler.close()


@shared_task(
    bind=True,
    name="apps.news.tasks.fetch_article",
    autoretry_for=(CrawlerError, OSError),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    rate_limit="20/m",
)
def fetch_article(self, portal: str, url: str) -> int | None:
    url = normalize_url(url)
    crawler = None
    try:
        crawler = get_crawler(portal)
        parsed = crawler.parse_article(crawler.fetch(url), url)
        if not parsed.get("title"):
            raise CrawlerError(f"Empty title for {url}")
        article, created = Article.objects.get_or_create(
            url=parsed["url"],
            defaults={
                "portal": parsed["portal"],
                "title": parsed["title"],
                "body": parsed.get("body") or "",
                "raw_date": parsed.get("raw_date") or "",
                "published_at": parsed.get("published_at"),
            },
        )
        if created:
            from apps.analysis.tasks import categorize_article

            categorize_article.delay(article.id)
        return article.id
    except Exception as exc:  # noqa: BLE001
        logger.exception("fetch_article failed for %s", url)
        run = start_run("news", portal=portal, task_id=self.request.id or "")
        finish_failed(run, f"{url}: {exc}")
        raise
    finally:
        if crawler is not None:
            crawler.close()
