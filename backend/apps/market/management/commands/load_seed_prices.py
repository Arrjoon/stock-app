import json
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.companies.models import Company
from apps.market.persist import upsert_prices


class Command(BaseCommand):
    help = "Load fixture OHLCV when live NEPSE sources are unreachable."

    def handle(self, *args, **options):
        path = Path(settings.BASE_DIR) / "tests" / "fixtures" / "nepse" / "price_history.json"
        payload = json.loads(path.read_text())
        template = payload.get("template") or []
        days = settings.MARKET_PRICE_DAYS
        count = 0
        for company in Company.objects.filter(active=True):
            rows = payload.get(company.symbol)
            if not rows:
                rows = []
                for offset in range(days):
                    trade_date = date.today() - timedelta(days=offset)
                    if trade_date.weekday() >= 5:
                        continue
                    sample = template[offset % len(template)] if template else {
                        "open": "100.00",
                        "high": "102.00",
                        "low": "99.00",
                        "close": "101.00",
                        "volume": 1000,
                    }
                    rows.append(
                        {
                            "date": trade_date.isoformat(),
                            **sample,
                        }
                    )
            parsed = [
                {
                    "date": date.fromisoformat(str(row["date"])[:10]),
                    "open": Decimal(str(row["open"])),
                    "high": Decimal(str(row["high"])),
                    "low": Decimal(str(row["low"])),
                    "close": Decimal(str(row["close"])),
                    "volume": int(row["volume"]),
                    "turnover": Decimal(str(row["turnover"])) if row.get("turnover") else None,
                    "trades": row.get("trades"),
                }
                for row in rows
            ]
            count += upsert_prices(company, parsed)
        self.stdout.write(f"seeded {count} price rows")
