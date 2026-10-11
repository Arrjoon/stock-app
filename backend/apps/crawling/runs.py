from __future__ import annotations

import logging

from django.utils import timezone

from apps.crawling.models import CrawlRun

logger = logging.getLogger(__name__)


def start_run(kind: str, portal: str = "", run_id=None, task_id: str = "") -> CrawlRun:
    if run_id:
        run = CrawlRun.objects.get(pk=run_id)
    else:
        run = CrawlRun.objects.create(kind=kind, portal=portal, status=CrawlRun.Status.QUEUED)
    run.status = CrawlRun.Status.RUNNING
    if task_id:
        run.celery_task_id = task_id
    run.save(update_fields=["status", "celery_task_id"])
    return run


def finish_success(run: CrawlRun, items: int, error: str = "") -> CrawlRun:
    run.status = CrawlRun.Status.SUCCESS
    run.items = items
    run.error = error
    run.finished_at = timezone.now()
    run.save(update_fields=["status", "items", "error", "finished_at"])
    return run


def finish_failed(run: CrawlRun, error: str, items: int = 0) -> CrawlRun:
    logger.error("CrawlRun %s failed: %s", run.pk, error)
    run.status = CrawlRun.Status.FAILED
    run.items = items
    run.error = error
    run.finished_at = timezone.now()
    run.save(update_fields=["status", "items", "error", "finished_at"])
    return run
