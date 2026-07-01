def _create_book(client, auth, **overrides):
    payload = {"title": "Dune", "author": "Frank Herbert", "total_pages": 400}
    payload.update(overrides)
    return client.post("/api/v1/books", headers=auth["headers"], json=payload)


def test_create_and_get_book(client, auth):
    resp = _create_book(client, auth)
    assert resp.status_code == 201
    book = resp.json()["data"]
    assert book["status"] == "currently_reading"

    got = client.get(f"/api/v1/books/{book['id']}", headers=auth["headers"])
    assert got.status_code == 200
    assert got.json()["data"]["title"] == "Dune"


def test_list_books_and_search(client, auth):
    _create_book(client, auth, title="Dune", author="Herbert")
    _create_book(client, auth, title="Piranesi", author="Clarke")
    resp = client.get("/api/v1/books?q=pira", headers=auth["headers"])
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Piranesi"


def test_update_book_rejects_already_read(client, auth):
    book = _create_book(client, auth).json()["data"]
    resp = client.patch(
        f"/api/v1/books/{book['id']}",
        headers=auth["headers"],
        json={"status": "already_read"},
    )
    assert resp.status_code == 409


def test_update_current_page_out_of_range(client, auth):
    book = _create_book(client, auth, total_pages=100).json()["data"]
    resp = client.patch(
        f"/api/v1/books/{book['id']}", headers=auth["headers"], json={"current_page": 500}
    )
    assert resp.status_code == 422


def test_other_users_book_is_forbidden(client, auth):
    book = _create_book(client, auth).json()["data"]
    other = client.post(
        "/api/v1/auth/signup",
        json={"email": "other@b.com", "password": "hunter2a", "display_name": "O"},
    ).json()["data"]
    headers = {"Authorization": f"Bearer {other['access_token']}"}
    resp = client.get(f"/api/v1/books/{book['id']}", headers=headers)
    assert resp.status_code == 403


def test_delete_book(client, auth):
    book = _create_book(client, auth).json()["data"]
    resp = client.delete(f"/api/v1/books/{book['id']}", headers=auth["headers"])
    assert resp.status_code == 200
    assert client.get(f"/api/v1/books/{book['id']}", headers=auth["headers"]).status_code == 404
