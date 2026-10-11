from __future__ import annotations

from apps.companies.models import Company
from apps.market.models import Floorsheet, Price


def upsert_prices(company: Company, rows: list[dict]) -> int:
    objects = [
        Price(
            company=company,
            date=row["date"],
            open=row["open"],
            high=row["high"],
            low=row["low"],
            close=row["close"],
            volume=row["volume"],
            turnover=row.get("turnover"),
            trades=row.get("trades"),
        )
        for row in rows
    ]
    if not objects:
        return 0
    try:
        Price.objects.bulk_create(
            objects,
            update_conflicts=True,
            unique_fields=["company", "date"],
            update_fields=["open", "high", "low", "close", "volume", "turnover", "trades"],
        )
    except Exception:  # noqa: BLE001 — composite PK backends differ
        for obj in objects:
            Price.objects.update_or_create(
                company=obj.company,
                date=obj.date,
                defaults={
                    "open": obj.open,
                    "high": obj.high,
                    "low": obj.low,
                    "close": obj.close,
                    "volume": obj.volume,
                    "turnover": obj.turnover,
                    "trades": obj.trades,
                },
            )
    return len(objects)


def insert_floorsheets(company: Company, rows: list[dict]) -> int:
    objects = [
        Floorsheet(
            company=company,
            date=row["date"],
            contract_no=row.get("contract_no") or "",
            buyer_broker=row["buyer_broker"],
            seller_broker=row["seller_broker"],
            qty=row["qty"],
            rate=row["rate"],
            amount=row.get("amount"),
        )
        for row in rows
    ]
    if not objects:
        return 0
    Floorsheet.objects.bulk_create(objects, batch_size=1000, ignore_conflicts=True)
    return len(objects)
