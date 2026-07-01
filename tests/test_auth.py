def test_signup_returns_tokens_and_user(client):
    resp = client.post(
        "/api/v1/auth/signup",
        json={"email": "a@b.com", "password": "hunter2a", "display_name": "  A  "},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["user"]["display_name"] == "A"
    assert body["data"]["access_token"]
    assert body["data"]["token_type"] == "bearer"


def test_signup_duplicate_email_conflicts(client):
    payload = {"email": "dup@b.com", "password": "hunter2a", "display_name": "A"}
    client.post("/api/v1/auth/signup", json=payload)
    resp = client.post("/api/v1/auth/signup", json=payload)
    assert resp.status_code == 409
    assert resp.json()["success"] is False


def test_signup_weak_password_422(client):
    resp = client.post(
        "/api/v1/auth/signup",
        json={"email": "a@b.com", "password": "short", "display_name": "A"},
    )
    assert resp.status_code == 422
    assert "errors" in resp.json()["data"]


def test_login_wrong_password_401(client):
    client.post(
        "/api/v1/auth/signup",
        json={"email": "a@b.com", "password": "hunter2a", "display_name": "A"},
    )
    resp = client.post("/api/v1/auth/login", json={"email": "a@b.com", "password": "wrongpass1"})
    assert resp.status_code == 401
    assert resp.json()["message"] == "Invalid email or password"


def test_refresh_rotates_and_reuse_detected(client):
    signup = client.post(
        "/api/v1/auth/signup",
        json={"email": "a@b.com", "password": "hunter2a", "display_name": "A"},
    ).json()["data"]
    old_refresh = signup["refresh_token"]

    first = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert first.status_code == 200
    new_refresh = first.json()["data"]["refresh_token"]
    assert new_refresh != old_refresh

    # Reusing the rotated token is rejected.
    reuse = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert reuse.status_code == 401

    # And the whole family is revoked.
    followup = client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})
    assert followup.status_code == 401


def test_protected_route_requires_auth(client):
    resp = client.get("/api/v1/users/me")
    assert resp.status_code == 401


def test_password_reset_request_always_200(client):
    resp = client.post("/api/v1/auth/password-reset/request", json={"email": "nobody@b.com"})
    assert resp.status_code == 200
