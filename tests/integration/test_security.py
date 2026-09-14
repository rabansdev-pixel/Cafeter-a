import re

import pytest
from flask import render_template_string, request

from app import create_app


@pytest.mark.parametrize("token", [None, "invalid-signature"])
def test_cart_rejects_missing_or_invalid_csrf(client, token):
    headers = {"X-CSRFToken": token} if token else {}
    response = client.post("/api/cart/calculate", json={}, headers=headers)
    assert response.status_code == 400
    assert response.get_json()["status"] == "error"
    assert "Recarga" in response.get_json()["message"]


def test_csrf_token_is_bound_to_client_session(app, client, csrf_headers):
    other_client = app.test_client()
    other_client.get("/")
    response = other_client.post(
        "/api/cart/calculate", json={}, headers=csrf_headers
    )
    assert response.status_code == 400
    assert (
        client.post(
            "/api/cart/calculate", json={}, headers=csrf_headers
        ).status_code
        == 200
    )


def test_expired_csrf_token_is_rejected(
    app, client, csrf_headers, monkeypatch
):
    monkeypatch.setitem(app.config, "WTF_CSRF_TIME_LIMIT", -1)
    response = client.post(
        "/api/cart/calculate", json={}, headers=csrf_headers
    )
    assert response.status_code == 400


def test_html_form_requires_and_accepts_csrf_token():
    app = create_app("testing")

    @app.route("/form", methods=["GET", "POST"])
    def form():
        if request.method == "POST":
            return "submitted"
        return render_template_string(
            '<input name="csrf_token" value="{{ csrf_token() }}">'
        )

    client = app.test_client()
    assert client.post("/form").status_code == 400
    page = client.get("/form").get_data(as_text=True)
    token = re.search(r'value="([^"]+)"', page).group(1)
    response = client.post("/form", data={"csrf_token": token})
    assert response.status_code == 200
    assert response.data == b"submitted"


@pytest.mark.parametrize("method", ["GET", "HEAD", "OPTIONS"])
def test_read_only_endpoints_need_no_csrf(client, method):
    response = client.open("/api/health", method=method)
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "script-src 'self'" in response.headers["Content-Security-Policy"]


def test_https_csrf_rejects_foreign_referrer(client):
    page = client.get("/", base_url="https://localhost").get_data(as_text=True)
    token = re.search(r'name="csrf-token" content="([^"]+)"', page).group(1)
    for referrer, expected in [
        ("https://attacker.example/", 400),
        ("https://localhost/", 200),
    ]:
        response = client.post(
            "/api/cart/calculate",
            json={},
            base_url="https://localhost",
            headers={"X-CSRFToken": token, "Referer": referrer},
        )
        assert response.status_code == expected
