def test_register_and_remove_token(client, auth):
    resp = client.post(
        "/api/v1/notifications/token",
        headers=auth["headers"],
        json={"token": "fcm-token-123", "platform": "android"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["token_registered"] is True

    removed = client.delete(
        "/api/v1/notifications/token?token=fcm-token-123", headers=auth["headers"]
    )
    assert removed.status_code == 200


def test_notification_history_from_finish(client, auth):
    # Finishing 5 books crosses a world-stage threshold, which stores a
    # notification in Supabase (the memory store here).
    for i in range(5):
        book = client.post(
            "/api/v1/books",
            headers=auth["headers"],
            json={"title": f"B{i}", "author": "A", "total_pages": 10},
        ).json()["data"]
        client.post(
            f"/api/v1/books/{book['id']}/finish",
            headers=auth["headers"],
            json={"summary": "done"},
        )

    resp = client.get("/api/v1/notifications", headers=auth["headers"])
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["unread_count"] >= 1
    assert data["items"][0]["data"]["type"] == "world_stage"


def test_mark_read_and_read_all(client, auth):
    book = None
    for i in range(5):
        book = client.post(
            "/api/v1/books",
            headers=auth["headers"],
            json={"title": f"B{i}", "author": "A", "total_pages": 10},
        ).json()["data"]
        client.post(
            f"/api/v1/books/{book['id']}/finish",
            headers=auth["headers"],
            json={"summary": "done"},
        )

    listing = client.get("/api/v1/notifications", headers=auth["headers"]).json()["data"]
    note_id = listing["items"][0]["id"]

    marked = client.patch(f"/api/v1/notifications/{note_id}/read", headers=auth["headers"])
    assert marked.status_code == 200
    assert marked.json()["data"]["is_read"] is True

    read_all = client.post("/api/v1/notifications/read-all", headers=auth["headers"])
    assert read_all.status_code == 200
    assert read_all.json()["data"]["unread_count"] == 0


def test_delete_notification(client, auth):
    for i in range(5):
        book = client.post(
            "/api/v1/books",
            headers=auth["headers"],
            json={"title": f"B{i}", "author": "A", "total_pages": 10},
        ).json()["data"]
        client.post(
            f"/api/v1/books/{book['id']}/finish",
            headers=auth["headers"],
            json={"summary": "done"},
        )
    listing = client.get("/api/v1/notifications", headers=auth["headers"]).json()["data"]
    note_id = listing["items"][0]["id"]
    resp = client.delete(f"/api/v1/notifications/{note_id}", headers=auth["headers"])
    assert resp.status_code == 200
