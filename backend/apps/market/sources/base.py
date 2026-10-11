from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime
from decimal import Decimal, InvalidOperation


class MarketDataSource(ABC):
    name = "unknown"

    @abstractmethod
    def fetch_prices(self, symbol: str, days: int) -> list[dict]:
        """Return OHLCV dicts with date, open, high, low, close, volume."""

    @abstractmethod
    def fetch_floorsheet(self, symbol: str, trade_date: date) -> list[dict]:
        """Return trades with buyer_broker, seller_broker, qty, rate."""


def pick(payload: dict, *keys, default=None):
    lower = {str(key).lower(): value for key, value in payload.items()}
    for key in keys:
        if key.lower() in lower and lower[key.lower()] not in (None, ""):
            return lower[key.lower()]
    return default


def as_decimal(value):
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value).replace(",", ""))
    except (InvalidOperation, ValueError, TypeError):
        return None


def as_int(value, default=0):
    if value in (None, ""):
        return default
    try:
        return int(float(str(value).replace(",", "")))
    except (TypeError, ValueError):
        return default


def as_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value)[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None
