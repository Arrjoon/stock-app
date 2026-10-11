from django.conf import settings

from apps.crawling.models import CrawlRun
from apps.market.tasks import crawl_floorsheet, crawl_prices
from apps.news.tasks import crawl_portal_news

ACTIVE = (CrawlRun.Status.QUEUED, CrawlRun.Status.RUNNING)


def enqueue_sync(user=None, *, news=True, prices=True, floorsheet=True) -> list[dict]:
    """Queue crawl tasks. A kind that is already queued or running is left alone."""
    queued = []
    if news:
        for portal, cfg in settings.CRAWLER_CONFIG.items():
            if cfg.get("enabled"):
                queued.append(_enqueue(CrawlRun.Kind.NEWS, portal, crawl_portal_news, (portal,), user))
    if prices:
        queued.append(_enqueue(CrawlRun.Kind.PRICES, "nepse", crawl_prices, (), user))
    if floorsheet:
        queued.append(_enqueue(CrawlRun.Kind.FLOORSHEET, "nepse", crawl_floorsheet, (), user))
    return queued


def enqueue_missing() -> list[dict]:
    """Start the first fetch when a table is still empty. Beat keeps the later schedule."""
    from apps.market.models import Floorsheet, Price
    from apps.news.models import Article

    if Price.objects.exists() and Floorsheet.objects.exists() and Article.objects.exists():
        return []
    return enqueue_sync(
        news=not Article.objects.exists(),
        prices=not Price.objects.exists(),
        floorsheet=not Floorsheet.objects.exists(),
    )


def _enqueue(kind: str, portal: str, task, args: tuple, user) -> dict:
    existing = (
        CrawlRun.objects.filter(kind=kind, portal=portal, status__in=ACTIVE)
        .order_by("-started_at")
        .first()
    )
    if existing is not None:
        return _row(existing, already_running=True)
    run = CrawlRun.objects.create(kind=kind, portal=portal, triggered_by=user)
    result = task.delay(*args, run.id)
    run.celery_task_id = result.id or ""
    run.save(update_fields=["celery_task_id"])
    return _row(run, already_running=False)


def _row(run: CrawlRun, already_running: bool) -> dict:
    return {
        "id": run.id,
        "kind": run.kind,
        "portal": run.portal,
        "status": run.status,
        "already_running": already_running,
    }
