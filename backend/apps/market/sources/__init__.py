from __future__ import annotations

import logging

from apps.market.sources.base import MarketDataSource
from apps.market.sources.merolagani import MeroLaganiMarketSource
from apps.market.sources.nepse import NepseClientSource

logger = logging.getLogger(__name__)


class FallbackMarketSource(MarketDataSource):
    name = "fallback"

    def __init__(self, primary: MarketDataSource, fallback: MarketDataSource):
        self.primary = primary
        self.fallback = fallback

    def fetch_prices(self, symbol: str, days: int) -> list[dict]:
        try:
            rows = self.primary.fetch_prices(symbol, days)
            if rows:
                return rows
        except Exception as exc:  # noqa: BLE001
            logger.warning("%s prices failed for %s: %s", self.primary.name, symbol, exc)
        return self.fallback.fetch_prices(symbol, days)

    def fetch_floorsheet(self, symbol: str, trade_date):
        try:
            rows = self.primary.fetch_floorsheet(symbol, trade_date)
            if rows:
                return rows
        except Exception as exc:  # noqa: BLE001
            logger.warning("%s floorsheet failed for %s: %s", self.primary.name, symbol, exc)
        return self.fallback.fetch_floorsheet(symbol, trade_date)


def get_market_source() -> MarketDataSource:
    return FallbackMarketSource(NepseClientSource(), MeroLaganiMarketSource())
