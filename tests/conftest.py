import os

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-ci-only")
os.environ.setdefault("FIREBASE_CREDENTIALS_JSON", "")

import pytest
from fastapi.testclient import TestClient

from app.db import container


@pytest.fixture(autouse=True)
def fresh_repos():
    """Reset to a clean in-memory database before each test."""
    container.use_memory()
    yield
    container.set_repositories(None)


@pytest.fixture
def client():
    from app.main import app

    return TestClient(app, raise_server_exceptions=False)


def _register(client, email="reader@bookworm.app", premium=False):
    resp = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "hunter2a", "display_name": "Sadia"},
    )
    data = resp.json()["data"]
    if premium:
        # Flip the premium flag directly in the in-memory store.
        repos = container.get_repositories()
        repos.users.update(data["user"]["id"], {"is_premium": True})
    return data


@pytest.fixture
def auth(client):
    data = _register(client)
    return {
        "headers": {"Authorization": f"Bearer {data['access_token']}"},
        "user": data["user"],
        "tokens": data,
    }


@pytest.fixture
def premium_auth(client):
    data = _register(client, email="premium@bookworm.app", premium=True)
    return {
        "headers": {"Authorization": f"Bearer {data['access_token']}"},
        "user": data["user"],
    }
