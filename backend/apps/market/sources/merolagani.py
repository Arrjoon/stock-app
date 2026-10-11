from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from apps.crawling.base import BaseCrawler
from apps.market.sources.base import MarketDataSource, as_date, as_decimal, as_int, pick
from apps.news.parsers import _text

logger = logging.getLogger(__name__)


class _Fetcher(BaseCrawler):
    portal = "merolagani"

    def list_article_urls(self) -> list[str]:
        return []

    def parse_article(self, html: str, url: str) -> dict:
        return {}


class MeroLaganiMarketSource(MarketDataSource):
    name = "merolagani"

    def __init__(self, fetcher=None):
        self.fetcher = fetcher or _Fetcher()

    def fetch_prices(self, symbol: str, days: int) -> list[dict]:
        endpoint = self.fetcher.config["price_history_url"]
        query = urlencode({"type": "get_company_graph", "symbol": symbol, "dateRange": 12})
        payload = self.fetcher.fetch(f"{endpoint}?{query}")
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            logger.warning("MeroLagani price JSON invalid for %s", symbol)
            return []
        quotes = data.get("quotes") or data.get("data") or []
        cutoff = date.today() - timedelta(days=max(days, 1))
        parsed = []
        for item in quotes:
            if not isinstance(item, dict):
                continue
            trade_date = as_date(pick(item, "date"))
            close = as_decimal(pick(item, "close"))
            if not trade_date or close is None or trade_date < cutoff:
                continue
            parsed.append(
                {
                    "date": trade_date,
                    "open": as_decimal(pick(item, "open")) or close,
                    "high": as_decimal(pick(item, "high")) or close,
                    "low": as_decimal(pick(item, "low")) or close,
                    "close": close,
                    "volume": as_int(pick(item, "volumen", "volume")),
                    "turnover": None,
                    "trades": None,
                }
            )
        return parsed

    def fetch_floorsheet(self, symbol: str, trade_date: date) -> list[dict]:
        html = self.fetcher.fetch(self.fetcher.config["floorsheet_url"])
        return parse_floorsheet_table(html, symbol, trade_date)


def parse_floorsheet_table(html: str, symbol: str, trade_date: date) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if not table:
        return []
    rows = []
    for tr in table.find_all("tr"):
        cells = [_text(td) for td in tr.find_all(["td", "th"])]
        mapped = _map_floorsheet_row(cells, symbol)
        if not mapped:
            continue
        qty = as_int(mapped["qty"])
        rate = as_decimal(mapped["rate"])
        if not qty or rate is None:
            continue
        rows.append(
            {
                "date": trade_date,
                "contract_no": str(mapped["contract_no"] or ""),
                "buyer_broker": str(mapped["buyer_broker"] or "")[:10],
                "seller_broker": str(mapped["seller_broker"] or "")[:10],
                "qty": qty,
                "rate": rate,
                "amount": as_decimal(mapped.get("amount")),
            }
        )
    return rows


def _map_floorsheet_row(cells, symbol):
    if len(cells) < 6 or cells[0] in {"#", "S.N.", "SN"}:
        return None
    if len(cells) >= 7 and cells[2].upper() == symbol.upper():
        return {
            "contract_no": cells[1],
            "symbol": cells[2],
            "buyer_broker": cells[3],
            "seller_broker": cells[4],
            "qty": cells[5],
            "rate": cells[6],
            "amount": cells[7] if len(cells) > 7 else None,
        }
    for idx, cell in enumerate(cells):
        if cell.upper() == symbol.upper() and idx + 4 < len(cells):
            return {
                "contract_no": cells[idx - 1] if idx else "",
                "symbol": cell,
                "buyer_broker": cells[idx + 1],
                "seller_broker": cells[idx + 2],
                "qty": cells[idx + 3],
                "rate": cells[idx + 4],
                "amount": cells[idx + 5] if idx + 5 < len(cells) else None,
            }
    return None
