from datetime import date
from decimal import Decimal

import pytest
from django.db import connection, IntegrityError

from apps.companies.models import Company
from apps.market.models import Price
from apps.news.models import Article, ArticleTag


@pytest.fixture
def company(db):
    return Company.objects.create(
        symbol="NABIL",
        name="Nabil Bank Limited",
        aliases=["Nabil"],
    )


def _price_kwargs(company, trade_date=date(2026, 1, 5)):
    return {
        "company": company,
        "date": trade_date,
        "open": Decimal("500.00"),
        "high": Decimal("510.00"),
        "low": Decimal("495.00"),
        "close": Decimal("505.00"),
        "volume": 1000,
    }


@pytest.mark.django_db(transaction=True)
def test_article_url_is_unique():
    Article.objects.create(
        url="https://example.com/nabil-news",
        portal="merolagani",
        title="Nabil update",
    )
    with pytest.raises(IntegrityError):
        Article.objects.create(
            url="https://example.com/nabil-news",
            portal="sharesansar",
            title="Duplicate URL",
        )


@pytest.mark.django_db(transaction=True)
def test_article_tag_unique_per_article_and_company(company):
    article = Article.objects.create(
        url="https://example.com/nabil-tag",
        portal="bizmandu",
        title="Tag test",
    )
    ArticleTag.objects.create(article=article, company=company, confidence=0.9)
    with pytest.raises(IntegrityError):
        ArticleTag.objects.create(article=article, company=company, confidence=0.4)


@pytest.mark.django_db(transaction=True)
def test_price_rejects_duplicate_company_date(company):
    Price.objects.create(**_price_kwargs(company))
    with pytest.raises(IntegrityError):
        Price.objects.create(**_price_kwargs(company))


@pytest.mark.django_db
def test_price_table_is_hypertable():
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT hypertable_name
            FROM timescaledb_information.hypertables
            WHERE hypertable_name = 'market_price'
            """
        )
        row = cursor.fetchone()
    assert row is not None
    assert row[0] == "market_price"
