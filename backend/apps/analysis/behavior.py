from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

TOP_N = 5
ZSCORE_MIN_DAYS = 5
ZSCORE_WINDOW = 20
ANOMALY_Z = 2.5


def rank_brokers(trades) -> tuple[list[dict], list[dict]]:
    """Net buy and net sell from floorsheet rows for one company-day."""
    books: dict[str, dict] = defaultdict(
        lambda: {"buy_qty": 0, "sell_qty": 0, "buy_amount": 0.0, "sell_amount": 0.0}
    )
    for trade in trades:
        amount = _amount(trade)
        buyer = str(trade.buyer_broker or "").strip()
        seller = str(trade.seller_broker or "").strip()
        if buyer:
            books[buyer]["buy_qty"] += int(trade.qty)
            books[buyer]["buy_amount"] += amount
        if seller:
            books[seller]["sell_qty"] += int(trade.qty)
            books[seller]["sell_amount"] += amount

    rows = []
    for broker, book in books.items():
        rows.append(
            {
                "broker": broker,
                "buy_qty": book["buy_qty"],
                "sell_qty": book["sell_qty"],
                "net_qty": book["buy_qty"] - book["sell_qty"],
                "buy_amount": round(book["buy_amount"], 2),
                "sell_amount": round(book["sell_amount"], 2),
            }
        )
    buyers = sorted(rows, key=lambda row: (row["net_qty"], row["buy_qty"]), reverse=True)[:TOP_N]
    sellers = sorted(rows, key=lambda row: (row["net_qty"], -row["sell_qty"]))[:TOP_N]
    buyers = [row for row in buyers if row["net_qty"] > 0 or row["buy_qty"] > 0]
    sellers = [row for row in sellers if row["net_qty"] < 0 or row["sell_qty"] > 0]
    return buyers, sellers


def daily_bar_metrics(prices: list, news_by_date: dict, trades_by_date: dict) -> list[dict]:
    """One analysis row per price bar. prices must be sorted by date ascending."""
    ordered = sorted(prices, key=lambda row: row.date)
    pressures: list[float] = []
    volumes: list[int] = []
    results = []
    for index, price in enumerate(ordered):
        high = Decimal(price.high)
        low = Decimal(price.low)
        close = Decimal(price.close)
        volume = int(price.volume)
        typical = (high + low + close) / Decimal(3)
        vwap = typical.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        close_vs_vwap = float((close - vwap) / vwap * 100) if vwap else 0.0
        pressure = _pressure(high, low, close, volume)
        pressures.append(pressure)
        prior_volumes = volumes[-ZSCORE_WINDOW:]
        volumes.append(volume)
        zscore = _zscore(prior_volumes, volume)
        pressure_5d = None
        if len(pressures) >= 5:
            pressure_5d = sum(pressures[-5:]) / 5
        nxt = ordered[index + 1] if index + 1 < len(ordered) else None
        next_return = None
        next_volume = None
        if nxt is not None and close:
            next_return = float((Decimal(nxt.close) - close) / close * 100)
            if volume:
                next_volume = (int(nxt.volume) - volume) / volume * 100
        buyers, sellers = rank_brokers(trades_by_date.get(price.date, []))
        results.append(
            {
                "date": price.date,
                "vwap": vwap,
                "close_vs_vwap_pct": close_vs_vwap,
                "pressure": pressure,
                "pressure_5d": pressure_5d,
                "volume_zscore": zscore,
                "is_volume_anomaly": zscore is not None and zscore > ANOMALY_Z,
                "news_count": int(news_by_date.get(price.date, 0)),
                "next_day_return_pct": next_return,
                "next_day_volume_change_pct": next_volume,
                "top_buyers": buyers,
                "top_sellers": sellers,
            }
        )
    return results


def _pressure(high: Decimal, low: Decimal, close: Decimal, volume: int) -> float:
    span = high - low
    if span == 0:
        return 0.0
    location = ((close - low) - (high - close)) / span
    return float(location * volume)


def _zscore(prior: list[int], current: int) -> float | None:
    if len(prior) < ZSCORE_MIN_DAYS:
        return None
    mean = sum(prior) / len(prior)
    variance = sum((value - mean) ** 2 for value in prior) / len(prior)
    if variance == 0:
        return 0.0
    return (current - mean) / (variance ** 0.5)


def _amount(trade) -> float:
    if trade.amount is not None:
        return float(trade.amount)
    return float(trade.qty) * float(trade.rate)
