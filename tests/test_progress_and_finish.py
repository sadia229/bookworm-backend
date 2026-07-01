def _create_book(client, auth, **overrides):
    payload = {"title": "Dune", "author": "Herbert", "total_pages": 400}
    payload.update(overrides)
    return client.post("/api/v1/books", headers=auth["headers"], json=payload).json()["data"]


def test_log_progress_advances_page(client, auth):
    book = _create_book(client, auth)
    resp = client.post(
        f"/api/v1/books/{book['id']}/progress",
        headers=auth["headers"],
        json={"pages_read": 50, "minutes": 30},
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["book"]["current_page"] == 50
    assert data["book"]["progress"] == 0.125


def test_log_progress_clamps_to_total(client, auth):
    book = _create_book(client, auth, total_pages=100)
    resp = client.post(
        f"/api/v1/books/{book['id']}/progress",
        headers=auth["headers"],
        json={"pages_read": 5000},
    )
    assert resp.json()["data"]["book"]["current_page"] == 100


def test_finish_book_awards_points_and_progression(client, auth):
    book = _create_book(client, auth)
    resp = client.post(
        f"/api/v1/books/{book['id']}/finish",
        headers=auth["headers"],
        json={"summary": "Great read", "rating": 5},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["book"]["status"] == "already_read"
    assert data["progression"]["points_awarded"] == 10
    assert data["progression"]["books_completed"] == 1

    me = client.get("/api/v1/users/me", headers=auth["headers"]).json()["data"]
    assert me["points"] == 10
    assert me["books_completed"] == 1


def test_finish_requires_summary(client, auth):
    book = _create_book(client, auth)
    resp = client.post(
        f"/api/v1/books/{book['id']}/finish", headers=auth["headers"], json={"rating": 3}
    )
    assert resp.status_code == 422


def test_finish_twice_is_conflict(client, auth):
    book = _create_book(client, auth)
    client.post(
        f"/api/v1/books/{book['id']}/finish",
        headers=auth["headers"],
        json={"summary": "done"},
    )
    resp = client.post(
        f"/api/v1/books/{book['id']}/finish",
        headers=auth["headers"],
        json={"summary": "again"},
    )
    assert resp.status_code == 409


def test_world_stage_advances_after_five_books(client, auth):
    for i in range(5):
        book = _create_book(client, auth, title=f"Book {i}")
        client.post(
            f"/api/v1/books/{book['id']}/finish",
            headers=auth["headers"],
            json={"summary": "done"},
        )
    me = client.get("/api/v1/users/me", headers=auth["headers"]).json()["data"]
    assert me["books_completed"] == 5
    assert me["world_stage"] == 1


def test_progress_window_zero_filled(client, auth):
    resp = client.get("/api/v1/progress", headers=auth["headers"])
    assert resp.status_code == 200
    assert len(resp.json()["data"]["buckets"]) == 7
