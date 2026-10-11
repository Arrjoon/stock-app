from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from apps.analysis.behavior import daily_bar_metrics, rank_brokers
from apps.analysis.models import AnalysisResult
from apps.companies.models import Company
from apps.market.models import Floorsheet, Price


def _trade(buyer, seller, qty, rate, amount=None):
    return SimpleNamespace(
        buyer_broker=buyer,
        seller_broker=seller,
        qty=qty,
        rate=Decimal(str(rate)),
        amount=None if amount is None else Decimal(str(amount)),
    )


def _price(day, close, volume, high=None, low=None):
    close = Decimal(str(close))
    return SimpleNamespace(
        date=day,
        high=Decimal(str(high if high is not None else close)),
        low=Decimal(str(low if low is not None else close)),
        close=close,
        volume=volume,
    )


def test_rank_brokers_net_buy_and_sell():
    trades = [
        _trade("58", "17", 100, "500", "50000"),
        _trade("58", "17", 50, "510", "25500"),
        _trade("17", "58", 20, "500", "10000"),
    ]
    buyers, sellers = rank_brokers(trades)
    assert buyers[0]["broker"] == "58"
    assert buyers[0]["net_qty"] == 130
    assert sellers[0]["broker"] == "17"
    assert sellers[0]["net_qty"] == -130


def test_pressure_and_volume_anomaly():
    volumes = [1000, 1200, 800, 1100, 900, 1000, 1050]
    prices = [
        _price(date(2026, 9, index + 1), 100, volume, high=110, low=90)
        for index, volume in enumerate(volumes)
    ]
    prices.append(_price(date(2026, 9, 8), 108, 20000, high=110, low=90))
    rows = daily_bar_metrics(prices, {date(2026, 9, 8): 3}, {})
    last = rows[-1]
    assert last["vwap"] == Decimal("102.67")
    assert last["pressure"] > 0
    assert last["pressure_5d"] is not None
    assert last["volume_zscore"] is not None
    assert last["volume_zscore"] > 2.5
    assert last["is_volume_anomaly"] is True
    assert last["news_count"] == 3
    assert rows[0]["next_day_return_pct"] == 0.0


def test_compute_persists_broker_ranks(db):
    from apps.analysis.compute import compute_company

    company = Company.objects.create(symbol="NABIL", name="Nabil Bank Limited", active=True)
    Price.objects.create(
        company=company,
        date=date(2026, 10, 9),
        open=Decimal("530"),
        high=Decimal("538"),
        low=Decimal("531"),
        close=Decimal("536.20"),
        volume=48000,
    )
    Floorsheet.objects.create(
        company=company,
        date=date(2026, 10, 9),
        contract_no="1",
        buyer_broker="58",
        seller_broker="17",
        qty=100,
        rate=Decimal("536.20"),
        amount=Decimal("53620"),
    )
    assert compute_company(company) == 1
    result = AnalysisResult.objects.get(company=company)
    assert result.top_buyers[0]["broker"] == "58"
    assert result.top_sellers[0]["broker"] == "17"
    assert result.vwap > 0
