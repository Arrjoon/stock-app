from __future__ import annotations

from collections import defaultdict

from django.utils import timezone

from apps.analysis.behavior import daily_bar_metrics
from apps.analysis.models import AnalysisResult
from apps.companies.models import Company
from apps.market.models import Floorsheet, Price
from apps.news.models import ArticleTag


def compute_company(company: Company) -> int:
    prices = list(Price.objects.filter(company=company).order_by("date"))
    if not prices:
        return 0
    trades_by_date = defaultdict(list)
    for trade in Floorsheet.objects.filter(company=company).order_by("date"):
        trades_by_date[trade.date].append(trade)
    news_by_date = _news_counts(company)
    rows = daily_bar_metrics(prices, news_by_date, trades_by_date)
    for row in rows:
        payload = dict(row)
        trade_date = payload.pop("date")
        AnalysisResult.objects.update_or_create(
            company=company,
            date=trade_date,
            defaults=payload,
        )
    return len(rows)


def compute_active_companies() -> int:
    written = 0
    for company in Company.objects.filter(active=True).order_by("symbol"):
        written += compute_company(company)
    return written


def _news_counts(company: Company) -> dict:
    counts: dict = defaultdict(int)
    zone = timezone.get_current_timezone()
    tags = ArticleTag.objects.filter(company=company).select_related("article")
    for tag in tags:
        published = tag.article.published_at
        if published is None:
            continue
        local_date = timezone.localtime(published, zone).date()
        counts[local_date] += 1
    return counts
