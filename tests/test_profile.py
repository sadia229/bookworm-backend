def test_get_me(client, auth):
    resp = client.get("/api/v1/users/me", headers=auth["headers"])
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["email"] == "reader@bookworm.app"
    assert data["books_completed"] == 0


def test_update_me(client, auth):
    resp = client.patch(
        "/api/v1/users/me", headers=auth["headers"], json={"display_name": "New Name"}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["display_name"] == "New Name"


def test_update_me_empty_body_400(client, auth):
    # api-doc.md: empty body -> 400 "No fields provided to update".
    resp = client.patch("/api/v1/users/me", headers=auth["headers"], json={})
    assert resp.status_code == 400


def test_public_profile_hidden_name(client, auth):
    client.patch("/api/v1/users/me", headers=auth["headers"], json={"name_hidden": True})
    resp = client.get(f"/api/v1/users/{auth['user']['id']}", headers=auth["headers"])
    assert resp.status_code == 200
    assert resp.json()["data"]["display_name"] == "Anonymous Reader"


def test_public_profile_not_found(client, auth):
    resp = client.get(
        "/api/v1/users/00000000-0000-0000-0000-000000000000", headers=auth["headers"]
    )
    assert resp.status_code == 404
