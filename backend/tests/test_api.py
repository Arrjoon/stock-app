from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.companies.models import Company
from apps.market.models import Price
from apps.news.models import Article, ArticleTag


@pytest.fixture
def viewer(db):
    return User.objects.create_user(
        email="viewer-api@example.com",
        username="viewer-api",
        password="pass-viewer",
        role=User.Role.VIEWER,
    )


@pytest.fixture
def analyst(db):
    return User.objects.create_user(
        email="analyst-api@example.com",
        username="analyst-api",
        password="pass-analyst",
        role=User.Role.ANALYST,
    )


@pytest.fixture
def nabil(db):
    return Company.objects.create(symbol="NABIL", name="Nabil Bank Limited", active=True)


def _auth(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_company_list_requires_auth():
    response = APIClient().get("/api/companies/")
    assert response.status_code == 401


@pytest.mark.django_db
def test_viewer_can_read_prices_and_compare(viewer, nabil):
    Price.objects.create(
        company=nabil,
        date=date(2026, 10, 8),
        open=Decimal("530"),
        high=Decimal("540"),
        low=Decimal("528"),
        close=Decimal("536"),
        volume=1000,
    )
    Price.objects.create(
        company=nabil,
        date=date(2026, 10, 9),
        open=Decimal("536"),
        high=Decimal("542"),
        low=Decimal("530"),
        close=Decimal("538"),
        volume=4000,
    )
    Price.objects.create(
        company=nabil,
        date=date(2026, 10, 10),
        open=Decimal("538"),
        high=Decimal("545"),
        low=Decimal("520"),
        close=Decimal("522"),
        volume=2500,
    )
    client = _auth(viewer)
    prices = client.get(f"/api/companies/{nabil.symbol}/prices/?range=30d")
    assert prices.status_code == 200
    assert prices.data["success"] is True
    assert len(prices.data["data"]) == 3
    compared = client.get("/api/compare/?range=30d")
    assert compared.status_code == 200
    assert compared.data["data"]["most_active"][0]["symbol"] == "NABIL"
    assert compared.data["data"]["most_volatile"][0]["volatility_pct"] > 0


@pytest.mark.django_db
def test_viewer_cannot_recategorize(viewer, analyst, nabil):
    article = Article.objects.create(
        url="https://example.com/nabil-api",
        portal="merolagani",
        title="Nabil update",
    )
    denied = _auth(viewer).post(f"/api/news/{article.id}/recategorize/", {"company_ids": [nabil.id]}, format="json")
    assert denied.status_code == 403
    allowed = _auth(analyst).post(
        f"/api/news/{article.id}/recategorize/",
        {"company_ids": [nabil.id]},
        format="json",
    )
    assert allowed.status_code == 200
    assert ArticleTag.objects.filter(article=article, company=nabil, source="manual").count() == 1


@pytest.mark.django_db
def test_bad_range_is_validation_error(viewer, nabil):
    response = _auth(viewer).get(f"/api/companies/{nabil.id}/prices/?range=2y")
    assert response.status_code == 400
    assert response.data["success"] is False
    assert response.data["error"]["code"] == "validation_error"
