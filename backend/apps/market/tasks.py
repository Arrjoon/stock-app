from __future__ import annotations

import logging
from datetime import date, timedelta

from celery import shared_task
from django.conf import settings

from apps.companies.models import Company
from apps.crawling.runs import finish_failed, finish_success, start_run
from apps.market.persist import insert_floorsheets, upsert_prices
from apps.market.sources import get_market_source

logger = logging.getLogger(__name__)


def _active_companies():
    return list(Company.objects.filter(active=True).order_by("symbol"))


@shared_task(bind=True, name="apps.market.tasks.crawl_prices")
def crawl_prices(self, run_id=None) -> int:
    run = start_run("prices", portal="nepse", run_id=run_id, task_id=self.request.id or "")
    source = get_market_source()
    days = settings.MARKET_PRICE_DAYS
    errors = []
    written = 0
    try:
        for company in _active_companies():
            try:
                rows = source.fetch_prices(company.symbol, days)
                written += upsert_prices(company, rows)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Price crawl failed for %s", company.symbol)
                errors.append(f"{company.symbol}: {exc}")
        summary = "\n".join(errors)
        if not _active_companies():
            finish_failed(run, "No active companies. Run sync_companies.", items=0)
            return 0
        if errors and written == 0:
            finish_failed(run, summary, items=0)
            return 0
        finish_success(run, items=written, error=summary)
        return written
    except Exception as exc:  # noqa: BLE001
        finish_failed(run, str(exc), items=written)
        raise


@shared_task(bind=True, name="apps.market.tasks.crawl_floorsheet")
def crawl_floorsheet(self, run_id=None) -> int:
    run = start_run("floorsheet", portal="nepse", run_id=run_id, task_id=self.request.id or "")
    source = get_market_source()
    sample_days = max(settings.MARKET_FLOORSHEET_DAYS, 1)
    dates = [date.today() - timedelta(days=offset) for offset in range(sample_days)]
    errors = []
    written = 0
    try:
        for company in _active_companies():
            for trade_date in dates:
                try:
                    rows = source.fetch_floorsheet(company.symbol, trade_date)
                    written += insert_floorsheets(company, rows)
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Floorsheet crawl failed for %s %s", company.symbol, trade_date)
                    errors.append(f"{company.symbol} {trade_date}: {exc}")
        summary = "\n".join(errors)
        if errors and written == 0:
            finish_failed(run, summary or "No floorsheet rows", items=0)
            return 0
        finish_success(run, items=written, error=summary)
        from apps.analysis.tasks import compute_behavior

        compute_behavior.delay()
        return written
    except Exception as exc:  # noqa: BLE001
        finish_failed(run, str(exc), items=written)
        raise
