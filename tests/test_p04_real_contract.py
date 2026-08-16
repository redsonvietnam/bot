import json
from datetime import datetime, timezone

import pytest
import requests

from overlay import router_bot_overlay as overlay
from sidecar import app as sidecar_app


class FlaskRequestsAdapter:
    """requests.get-shaped adapter backed by Flask's in-process test client."""

    def __init__(self, client):
        self.client = client

    def get(self, url, **kwargs):
        response = self.client.get(url)
        return FlaskResponseAdapter(response)


class FlaskResponseAdapter:
    def __init__(self, response):
        self.status_code = response.status_code
        self._json = response.get_json()

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._json


@pytest.fixture
def sidecar_client(monkeypatch, tmp_path):
    monkeypatch.setattr(sidecar_app, "DB_JSON_PATH", str(tmp_path / "db.json"))
    monkeypatch.setattr(
        sidecar_app,
        "_last_good",
        {"state": "offline", "detail": "Chua doc duoc du lieu"},
    )
    return sidecar_app.app.test_client()


def _wire_sidecar_to_overlay(monkeypatch, client):
    adapter = FlaskRequestsAdapter(client)
    monkeypatch.setattr(overlay.requests, "get", adapter.get)


def test_real_sidecar_valid_status_reaches_overlay_parser(
    monkeypatch, sidecar_client, tmp_path
):
    db = {
        "providerConnections": [
            {
                "isActive": True,
                "testStatus": "available",
                "lastUsedAt": "2026-08-16T00:00:00+00:00",
                "modelLock___all": None,
            }
        ]
    }
    (tmp_path / "db.json").write_text(json.dumps(db), encoding="utf-8")
    fixed_now = datetime(2026, 8, 16, 0, 0, 10, tzinfo=timezone.utc)
    monkeypatch.setattr(sidecar_app, "_now_utc", lambda: fixed_now)
    _wire_sidecar_to_overlay(monkeypatch, sidecar_client)

    assert overlay._fetch_status() == (
        "active",
        "Dang hoat dong - 1/1 connections kha dung",
    )


def test_real_sidecar_fallback_status_reaches_overlay_parser(
    monkeypatch, sidecar_client
):
    fallback = {"state": "warning", "detail": "cached fallback"}
    monkeypatch.setattr(sidecar_app, "_last_good", fallback)
    # Missing DB path forces the real /api/status route into its fallback path.
    _wire_sidecar_to_overlay(monkeypatch, sidecar_client)

    assert overlay._fetch_status() == ("warning", "cached fallback")


def test_real_sidecar_invalid_contract_is_rejected_by_overlay(
    monkeypatch, sidecar_client
):
    monkeypatch.setattr(
        sidecar_app,
        "_compute_status",
        lambda: {"state": "not-a-valid-state", "detail": "bad contract"},
    )
    _wire_sidecar_to_overlay(monkeypatch, sidecar_client)

    with pytest.raises(ValueError, match="Unknown state"):
        overlay._fetch_status()
