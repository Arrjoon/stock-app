from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.crawling.models import CrawlRun
from apps.crawling.sync import enqueue_missing
from apps.companies.models import Company
from apps.market.models import Floorsheet, Price
from apps.news.models import Article


class _Result:
    id = "task-1"


@pytest.fixture
def admin(db):
    return User.objects.create_user(
        email="admin-sync@example.com",
        username="admin-sync",
        password="pass-admin",
        role=User.Role.ADMIN,
    )


@pytest.fixture
def viewer(db):
    return User.objects.create_user(
        email="viewer-sync@example.com",
        username="viewer-sync",
        password="pass-viewer",
        role=User.Role.VIEWER,
    )


def _auth(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_viewer_cannot_sync(viewer):
    response = _auth(viewer).post("/api/admin/sync/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_sync_queues_once(admin, monkeypatch):
    calls = []

    def fake_delay(*args):
        calls.append(args)
        return _Result()

    monkeypatch.setattr("apps.crawling.sync.crawl_prices.delay", fake_delay)
    monkeypatch.setattr("apps.crawling.sync.crawl_floorsheet.delay", fake_delay)
    monkeypatch.setattr("apps.crawling.sync.crawl_portal_news.delay", fake_delay)

    first = _auth(admin).post("/api/admin/sync/")
    assert first.status_code == 200
    assert first.data["success"] is True
    kinds = {row["kind"] for row in first.data["data"]}
    assert {"prices", "floorsheet", "news"} <= kinds
    assert all(row["already_running"] is False for row in first.data["data"])

    second = _auth(admin).post("/api/admin/sync/")
    assert second.status_code == 200
    assert all(row["already_running"] is True for row in second.data["data"])
    assert len(calls) == len(first.data["data"])


@pytest.mark.django_db
def test_bootstrap_skips_when_data_exists(monkeypatch):
    company = Company.objects.create(symbol="NABIL", name="Nabil Bank Limited", active=True)
    Price.objects.create(
        company=company,
        date=date(2026, 10, 9),
        open=Decimal("1"),
        high=Decimal("1"),
        low=Decimal("1"),
        close=Decimal("1"),
        volume=1,
    )
    Floorsheet.objects.create(
        company=company,
        date=date(2026, 10, 9),
        buyer_broker="1",
        seller_broker="2",
        qty=1,
        rate=Decimal("1"),
    )
    Article.objects.create(url="https://example.com/already", portal="merolagani", title="Have")

    def fail_delay(*_args):
        raise AssertionError("should not queue")

    monkeypatch.setattr("apps.crawling.sync.crawl_prices.delay", fail_delay)
    monkeypatch.setattr("apps.crawling.sync.crawl_floorsheet.delay", fail_delay)
    monkeypatch.setattr("apps.crawling.sync.crawl_portal_news.delay", fail_delay)
    assert enqueue_missing() == []
    assert CrawlRun.objects.count() == 0
