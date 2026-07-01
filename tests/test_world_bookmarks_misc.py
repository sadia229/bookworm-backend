def _finish_a_book(client, headers, title="Dune"):
    book = client.post(
        "/api/v1/books",
        headers=headers,
        json={"title": title, "author": "Herbert", "total_pages": 100},
    ).json()["data"]
    client.post(
        f"/api/v1/books/{book['id']}/finish", headers=headers, json={"summary": "done", "rating": 5}
    )
    return book


def test_world_premium_gate(client, auth):
    resp = client.get("/api/v1/world", headers=auth["headers"])
    assert resp.status_code == 403
    assert resp.json()["data"]["is_premium"] is False


def test_world_premium_ok(client, premium_auth):
    resp = client.get("/api/v1/world", headers=premium_auth["headers"])
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["world_stage"] == 0
    assert data["layers"]


def test_bookmark_flow(client, auth):
    # Owner finishes a book, another user bookmarks it.
    owner_book = _finish_a_book(client, auth["headers"])

    reader = client.post(
        "/api/v1/auth/signup",
        json={"email": "reader2@b.com", "password": "hunter2a", "display_name": "R"},
    ).json()["data"]
    headers = {"Authorization": f"Bearer {reader['access_token']}"}

    created = client.post(
        "/api/v1/bookmarks", headers=headers, json={"book_id": owner_book["id"]}
    )
    assert created.status_code == 201

    dup = client.post("/api/v1/bookmarks", headers=headers, json={"book_id": owner_book["id"]})
    assert dup.status_code == 409

    listing = client.get("/api/v1/bookmarks", headers=headers).json()["data"]
    assert listing["total"] == 1
    assert listing["items"][0]["book"]["title"] == "Dune"


def test_cannot_bookmark_own_book(client, auth):
    owner_book = _finish_a_book(client, auth["headers"])
    resp = client.post(
        "/api/v1/bookmarks", headers=auth["headers"], json={"book_id": owner_book["id"]}
    )
    assert resp.status_code == 400


def test_leaderboard_includes_me(client, auth):
    _finish_a_book(client, auth["headers"])
    resp = client.get("/api/v1/leaderboard", headers=auth["headers"])
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["me"]["user_id"] == auth["user"]["id"]
    assert data["items"][0]["is_current_user"] is True


def test_dashboard(client, auth):
    resp = client.get("/api/v1/stats/dashboard", headers=auth["headers"])
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["display_name"] == "Sadia"
    assert len(data["weekly_chart"]) == 7


def test_review_update_and_delete(client, auth):
    book = _finish_a_book(client, auth["headers"])
    upd = client.put(
        f"/api/v1/books/{book['id']}/review",
        headers=auth["headers"],
        json={"summary": "revised", "rating": 4},
    )
    assert upd.status_code == 200
    assert upd.json()["data"]["rating"] == 4

    removed = client.delete(f"/api/v1/books/{book['id']}/review", headers=auth["headers"])
    assert removed.status_code == 200


def test_public_shelf_shows_finished(client, auth):
    _finish_a_book(client, auth["headers"])
    resp = client.get(f"/api/v1/users/{auth['user']['id']}/books", headers=auth["headers"])
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] == 1
