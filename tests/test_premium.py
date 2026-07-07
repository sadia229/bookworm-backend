import pytest

from app.config import get_settings
from app.services import revenuecat_service

_SECRET = "whsec_test_123"


@pytest.fixture(autouse=True)
def _configure_revenuecat(monkeypatch):
    monkeypatch.setenv("REVENUECAT_WEBHOOK_SECRET", _SECRET)
    monkeypatch.setenv("REVENUECAT_API_KEY", "sk_test")
    monkeypatch.setenv("REVENUECAT_ENTITLEMENT_ID", "premium")
    monkeypatch.setenv("ENVIRONMENT", "development")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _event(user_id, event_type="INITIAL_PURCHASE", event_id="evt_1", **extra):
    event = {
        "id": event_id,
        "type": event_type,
        "app_user_id": user_id,
        "entitlement_ids": ["premium"],
        "expiration_at_ms": 1754524800000,
        "environment": "PRODUCTION",
    }
    event.update(extra)
    return {"event": event}


def _headers():
    return {"Authorization": _SECRET}


def test_webhook_grants_premium(client, auth):
    resp = client.post(
        "/api/v1/webhooks/revenuecat",
        headers=_headers(),
        json=_event(auth["user"]["id"]),
    )
    assert resp.status_code == 200
    me = client.get("/api/v1/users/me", headers=auth["headers"]).json()["data"]
    assert me["is_premium"] is True
    assert me["premium_until"] is not None


def test_webhook_expiration_revokes_premium(client, auth):
    client.post(
        "/api/v1/webhooks/revenuecat", headers=_headers(), json=_event(auth["user"]["id"])
    )
    client.post(
        "/api/v1/webhooks/revenuecat",
        headers=_headers(),
        json=_event(auth["user"]["id"], event_type="EXPIRATION", event_id="evt_2"),
    )
    me = client.get("/api/v1/users/me", headers=auth["headers"]).json()["data"]
    assert me["is_premium"] is False
    assert me["premium_until"] is None


def test_webhook_is_idempotent(client, auth):
    body = _event(auth["user"]["id"])
    client.post("/api/v1/webhooks/revenuecat", headers=_headers(), json=body)
    # Revoke directly, then replay the same (already-processed) grant event.
    repos = _repos()
    repos.users.update(auth["user"]["id"], {"is_premium": False})
    resp = client.post("/api/v1/webhooks/revenuecat", headers=_headers(), json=body)
    assert resp.status_code == 200
    me = client.get("/api/v1/users/me", headers=auth["headers"]).json()["data"]
    assert me["is_premium"] is False  # replay was a no-op


def test_webhook_bad_secret_401(client, auth):
    resp = client.post(
        "/api/v1/webhooks/revenuecat",
        headers={"Authorization": "wrong"},
        json=_event(auth["user"]["id"]),
    )
    assert resp.status_code == 401


def test_webhook_unknown_user_is_ok(client):
    resp = client.post(
        "/api/v1/webhooks/revenuecat",
        headers=_headers(),
        json=_event("00000000-0000-0000-0000-000000000000"),
    )
    assert resp.status_code == 200


def test_webhook_ignores_other_entitlement(client, auth):
    resp = client.post(
        "/api/v1/webhooks/revenuecat",
        headers=_headers(),
        json=_event(auth["user"]["id"], entitlement_ids=["some_other"]),
    )
    assert resp.status_code == 200
    me = client.get("/api/v1/users/me", headers=auth["headers"]).json()["data"]
    assert me["is_premium"] is False


def test_premium_sync_grants(client, auth, monkeypatch):
    monkeypatch.setattr(
        revenuecat_service, "fetch_premium_status", lambda uid: (True, "2026-08-07T00:00:00Z")
    )
    resp = client.post("/api/v1/users/me/premium/sync", headers=auth["headers"])
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["is_premium"] is True
    assert data["premium_until"] == "2026-08-07T00:00:00Z"


def test_premium_sync_unavailable_502(client, auth, monkeypatch):
    def _raise(uid):
        raise revenuecat_service.RevenueCatUnavailable("down")

    monkeypatch.setattr(revenuecat_service, "fetch_premium_status", _raise)
    resp = client.post("/api/v1/users/me/premium/sync", headers=auth["headers"])
    assert resp.status_code == 502


def _repos():
    from app.db import container

    return container.get_repositories()
