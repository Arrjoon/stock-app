from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from asgiref.sync import async_to_sync
from channels.layers import channel_layers, get_channel_layer
from channels.testing import WebsocketCommunicator
from django.test.utils import override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import User
from apps.companies.models import Company
from apps.news.models import Article, TagCorrection
from apps.realtime.notify import notify
from config.asgi import application

IN_MEMORY = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}


@pytest.fixture
def viewer(db):
    return User.objects.create_user(email="rbac-viewer@example.com", username="rbac-viewer", password="pass-viewer", role=User.Role.VIEWER)


@pytest.fixture
def analyst(db):
    return User.objects.create_user(email="rbac-analyst@example.com", username="rbac-analyst", password="pass-analyst", role=User.Role.ANALYST)


@pytest.fixture
def admin(db):
    return User.objects.create_user(email="rbac-admin@example.com", username="rbac-admin", password="pass-admin", role=User.Role.ADMIN)


@pytest.fixture
def nabil(db):
    return Company.objects.create(symbol="RBAC", name="RBAC Bank", active=True)


def _auth(user):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("user_name", "method", "path", "expected"),
    [
        (None, "get", "/api/admin/users/", 401),
        ("viewer", "get", "/api/admin/users/", 403),
        ("analyst", "get", "/api/admin/users/", 403),
        ("admin", "get", "/api/admin/users/", 200),
        (None, "get", "/api/admin/crawl-runs/", 401),
        ("viewer", "post", "/api/admin/crawl-runs/", 403),
        ("viewer", "get", "/api/companies/1/export/?format=json", 403),
    ],
)
def test_role_matrix(request, user_name, method, path, expected, viewer, analyst, admin, nabil):
    user = {"viewer": viewer, "analyst": analyst, "admin": admin}.get(user_name)
    path = path.replace("/api/companies/1/", f"/api/companies/{nabil.id}/")
    client = _auth(user)
    response = getattr(client, method)(path, {"kind": "prices"}, format="json")
    assert response.status_code == expected


@pytest.mark.django_db
def test_admin_crawl_returns_202(admin):
    with patch("apps.crawling.api_views.crawl_prices.delay", return_value=SimpleNamespace(id="task-1")):
        response = _auth(admin).post("/api/admin/crawl-runs/", {"kind": "prices"}, format="json")
    assert response.status_code == 202
    assert response.data["data"]["status"] == "queued"


@pytest.mark.django_db
def test_export_allows_analyst(analyst, nabil):
    from apps.market.models import Price

    Price.objects.create(company=nabil, date=date(2026, 10, 8), open=1, high=2, low=1, close=Decimal("2"), volume=10)
    response = _auth(analyst).get(f"/api/companies/{nabil.symbol}/export/?format=json")
    assert response.status_code == 200
    assert response.data["data"]["prices"]


@pytest.mark.django_db
def test_recategorize_writes_correction_and_rejects_unknown(analyst, nabil):
    article = Article.objects.create(url="https://example.com/rbac", portal="merolagani", title="RBAC note")
    denied = _auth(analyst).post(f"/api/news/{article.id}/recategorize/", {"company_ids": [999999]}, format="json")
    assert denied.status_code == 400
    ok = _auth(analyst).post(f"/api/news/{article.id}/recategorize/", {"company_ids": [nabil.id]}, format="json")
    assert ok.status_code == 200
    correction = TagCorrection.objects.get(article=article)
    assert correction.new_tags[0]["company_id"] == nabil.id
    assert correction.user_id == analyst.id


@pytest.mark.django_db
def test_notify_waits_for_commit(django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=False) as callbacks:
        notify("prices", symbol="RBAC")
    assert len(callbacks) == 1


@override_settings(CHANNEL_LAYERS=IN_MEMORY)
@pytest.mark.django_db(transaction=True)
def test_websocket_rejects_missing_token_and_receives_notify(viewer):
    token = str(AccessToken.for_user(viewer))

    async def _flow():
        channel_layers.backends.clear()
        rejected = WebsocketCommunicator(application, "/ws/updates")
        connected, _ = await rejected.connect()
        assert connected is False

        client = WebsocketCommunicator(application, f"/ws/updates?token={token}")
        connected, _ = await client.connect()
        assert connected is True
        await get_channel_layer().group_send(
            "dashboard",
            {"type": "dashboard.event", "payload": {"event": "prices", "symbol": "RBAC"}},
        )
        message = await client.receive_json_from(timeout=2)
        await client.disconnect()
        return message

    message = async_to_sync(_flow)()
    assert message["event"] == "prices"
