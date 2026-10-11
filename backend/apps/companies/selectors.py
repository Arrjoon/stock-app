from datetime import date, timedelta
from statistics import pstdev

from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.companies.models import Company
from apps.market.models import Price
from apps.news.models import Article


def get_active_company(key: str) -> Company:
    if str(key).isdigit():
        return get_object_or_404(Company, pk=int(key), active=True)
    return get_object_or_404(Company, symbol__iexact=key, active=True)


def parse_range_days(raw: str | None) -> int:
    value = (raw or "30d").strip().lower()
    allowed = {"7d": 7, "30d": 30, "90d": 90}
    if value not in allowed:
        from rest_framework.exceptions import ValidationError

        raise ValidationError({"range": "Use 7d, 30d, or 90d."})
    return allowed[value]


def comparison(days: int = 30) -> dict:
    since = date.today() - timedelta(days=days)
    zone = timezone.get_current_timezone()
    rows = []
    for company in Company.objects.filter(active=True).order_by("symbol"):
        prices = list(
            Price.objects.filter(company=company, date__gte=since).order_by("date")
        )
        returns = []
        for previous, current in zip(prices, prices[1:]):
            if previous.close:
                returns.append(float((current.close - previous.close) / previous.close))
        volatility = pstdev(returns) * 100 if len(returns) >= 2 else 0.0
        volume = sum(int(price.volume) for price in prices)
        news_count = (
            Article.objects.filter(tags__company=company, published_at__isnull=False)
            .filter(published_at__date__gte=since)
            .distinct()
            .count()
        )
        rows.append(
            {
                "id": company.id,
                "symbol": company.symbol,
                "name": company.name,
                "volatility_pct": round(volatility, 4),
                "volume": volume,
                "news_count": news_count,
            }
        )
    return {
        "range": f"{days}d",
        "as_of": timezone.localtime(timezone.now(), zone).date().isoformat(),
        "most_volatile": sorted(rows, key=lambda row: row["volatility_pct"], reverse=True),
        "most_active": sorted(rows, key=lambda row: row["volume"], reverse=True),
        "most_in_the_news": sorted(rows, key=lambda row: row["news_count"], reverse=True),
    }
