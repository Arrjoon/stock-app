from __future__ import annotations

import logging
from datetime import date, timedelta

from django.conf import settings

from apps.market.sources.base import MarketDataSource, as_date, as_decimal, as_int, pick

logger = logging.getLogger(__name__)


class NepseClientSource(MarketDataSource):
    name = "nepse-client"
    max_floorsheet_pages = 25

    def __init__(self, client=None):
        self._client = client
        self._company_sheet_blocked = False
        self._latest_sheet: list[dict] | None = None

    @property
    def client(self):
        if self._client is None:
            from nepse_client import NepseClient

            self._client = NepseClient()
            if not settings.NEPSE_TLS_VERIFY and hasattr(self._client, "setTLSVerification"):
                self._client.setTLSVerification(False)
        return self._client

    def fetch_prices(self, symbol: str, days: int) -> list[dict]:
        end = date.today()
        start = end - timedelta(days=max(days, 1))
        raw = self.client.getCompanyPriceVolumeHistory(
            symbol=symbol, start_date=start, end_date=end
        )
        rows = raw if isinstance(raw, list) else pick(raw or {}, "content", "data", "quotes") or []
        parsed = []
        for item in rows:
            if not isinstance(item, dict):
                continue
            trade_date = as_date(
                pick(item, "businessDate", "date", "tradedDate", "timestamp")
            )
            close = as_decimal(pick(item, "closePrice", "close", "lastTradedPrice"))
            if not trade_date or close is None:
                continue
            parsed.append(
                {
                    "date": trade_date,
                    "open": as_decimal(pick(item, "openPrice", "open")) or close,
                    "high": as_decimal(pick(item, "highPrice", "high")) or close,
                    "low": as_decimal(pick(item, "lowPrice", "low")) or close,
                    "close": close,
                    "volume": as_int(pick(item, "totalTradedQuantity", "volume", "volumen")),
                    "turnover": as_decimal(
                        pick(item, "totalTradedValue", "turnover", "amount")
                    ),
                    "trades": as_int(pick(item, "totalTrades", "trades"), default=None),
                }
            )
        return parsed

    def fetch_floorsheet(self, symbol: str, trade_date: date) -> list[dict]:
        if not self._company_sheet_blocked:
            try:
                raw = self.client.getFloorSheetOf(symbol=symbol, business_date=str(trade_date))
                parsed = self._parse_sheet_rows(raw, trade_date)
                if parsed:
                    return parsed
            except Exception as exc:  # noqa: BLE001
                self._company_sheet_blocked = True
                logger.warning(
                    "Company floorsheet endpoint failed (%s); sampling latest session",
                    exc,
                )
        return [
            row
            for row in self._latest_session_rows()
            if row["symbol"] == symbol.upper() and row["date"] == trade_date
        ]

    def _latest_session_rows(self) -> list[dict]:
        if self._latest_sheet is not None:
            return self._latest_sheet
        first = self.client.getFloorSheet(page=0)
        page = first if isinstance(first, dict) else {"content": first or [], "totalPages": 1}
        content = list(page.get("content") or [])
        total_pages = int(page.get("totalPages") or 1)
        limit = min(total_pages, self.max_floorsheet_pages)
        for page_no in range(1, limit):
            nxt = self.client.getFloorSheet(page=page_no)
            if isinstance(nxt, dict):
                content.extend(nxt.get("content") or [])
            elif isinstance(nxt, list):
                content.extend(nxt)
        parsed = []
        for item in content:
            row = self._parse_trade(item, None)
            if row:
                parsed.append(row)
        logger.info(
            "Sampled %s floorsheet rows from %s/%s pages",
            len(parsed),
            limit,
            total_pages,
        )
        self._latest_sheet = parsed
        return parsed

    def _parse_sheet_rows(self, raw, trade_date: date) -> list[dict]:
        rows = raw if isinstance(raw, list) else pick(raw or {}, "content", "data", "floorsheets") or []
        parsed = []
        for item in rows:
            row = self._parse_trade(item, trade_date)
            if row:
                parsed.append(row)
        return parsed

    def _parse_trade(self, item, trade_date: date | None) -> dict | None:
        if not isinstance(item, dict):
            return None
        qty = as_int(pick(item, "contractQuantity", "quantity", "qty"))
        rate = as_decimal(pick(item, "contractRate", "rate"))
        symbol = str(pick(item, "stockSymbol", "symbol") or "").upper()
        if not qty or rate is None:
            return None
        return {
            "symbol": symbol,
            "date": as_date(pick(item, "businessDate", "date")) or trade_date,
            "contract_no": str(pick(item, "contractId", "contractNo", "transactionNo") or ""),
            "buyer_broker": str(pick(item, "buyerMemberId", "buyerBroker", "buyer") or "")[:10],
            "seller_broker": str(pick(item, "sellerMemberId", "sellerBroker", "seller") or "")[:10],
            "qty": qty,
            "rate": rate,
            "amount": as_decimal(pick(item, "contractAmount", "amount")),
        }
