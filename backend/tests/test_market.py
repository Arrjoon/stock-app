from datetime import date
from decimal import Decimal

from apps.companies.models import Company
from apps.market.persist import upsert_prices
from apps.market.sources.merolagani import parse_floorsheet_table
from apps.market.models import Price


def test_price_upsert_is_idempotent(db):
    company = Company.objects.create(symbol="NABIL", name="Nabil Bank Limited")
    rows = [
        {
            "date": date(2026, 9, 11),
            "open": Decimal("500.00"),
            "high": Decimal("510.00"),
            "low": Decimal("495.00"),
            "close": Decimal("505.00"),
            "volume": 1500,
            "turnover": Decimal("757500.00"),
            "trades": 55,
        }
    ]
    upsert_prices(company, rows)
    upsert_prices(company, rows)
    assert Price.objects.filter(company=company).count() == 1


def test_floorsheet_table_filters_symbol():
    html = """
    <table>
      <tr><th>#</th><th>Transact. No.</th><th>Symbol</th><th>Buyer</th>
          <th>Seller</th><th>Quantity</th><th>Rate</th><th>Amount</th></tr>
      <tr><td>1</td><td>1001</td><td>NABIL</td><td>58</td><td>17</td>
          <td>100</td><td>508</td><td>50800</td></tr>
      <tr><td>2</td><td>1002</td><td>NICA</td><td>1</td><td>2</td>
          <td>10</td><td>400</td><td>4000</td></tr>
    </table>
    """
    rows = parse_floorsheet_table(html, "NABIL", date(2026, 9, 12))
    assert len(rows) == 1
    assert rows[0]["buyer_broker"] == "58"
    assert rows[0]["qty"] == 100
