import json
from datetime import datetime, timedelta, timezone

import pytest

from overlay import router_bot_overlay as overlay
from sidecar import app as sidecar_app
from tests.helpers import make_connections, write_db


def test_api_status_returns_last_good_state_when_db_is_missing(db_file):
    write_db(db_file, make_connections())
    expected = sidecar_app._compute_status()
    db_file.unlink()

    response = sidecar_app.app.test_client().get("/api/status")

    assert response.status_code == 200
    assert response.get_json() == expected


def test_api_status_returns_last_good_state_for_malformed_json(db_file):
    write_db(db_file, make_connections())
    expected = sidecar_app._compute_status()
    db_file.write_text('{"providerConnections": [', encoding="utf-8")

    response = sidecar_app.app.test_client().get("/api/status")

    assert response.status_code == 200
    assert response.get_json() == expected


def test_compute_status_rejects_non_object_db_root(db_file):
    db_file.write_text("[]", encoding="utf-8")

    try:
        sidecar_app._compute_status()
    except ValueError as exc:
        assert str(exc) == "db.json root must be an object"
    else:
        raise AssertionError("_compute_status() accepted a non-object DB root")


def test_compute_status_rejects_non_object_connections(db_file):
    write_db(db_file, make_connections())
    db = json.loads(db_file.read_text(encoding="utf-8"))
    db["providerConnections"].append("invalid")
    db_file.write_text(json.dumps(db), encoding="utf-8")

    try:
        sidecar_app._compute_status()
    except ValueError as exc:
        assert str(exc) == "providerConnections contains non-object entries"
    else:
        raise AssertionError("_compute_status() accepted a non-object connection")


def test_future_last_used_at_is_not_recent():
    future = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    connections = make_connections()
    connections[0]["lastUsedAt"] = future

    now = datetime.now(timezone.utc)
    assert sidecar_app._is_recent(connections[0], now) is False


def test_initial_cache_is_offline_when_db_is_unavailable(db_file):
    response = sidecar_app.app.test_client().get("/api/status")

    assert response.status_code == 200
    assert response.get_json() == {
        "state": "offline",
        "detail": "Chua doc duoc du lieu",
    }


def test_valid_db_recovers_after_initial_failure(db_file):
    db_file.write_text("{malformed", encoding="utf-8")
    assert sidecar_app.app.test_client().get("/api/status").get_json()["state"] == "offline"

    connections = make_connections()
    write_db(db_file, connections)
    result = sidecar_app.app.test_client().get("/api/status").get_json()

    assert result["state"] == "idle"
    assert result["detail"] == "San sang - 23/23 connections kha dung"


def test_overlay_accepts_known_state_payload():
    assert overlay._parse_status_payload({"state": "warning", "detail": "12/23"}) == (
        "warning",
        "12/23",
    )


@pytest.mark.parametrize("payload", [
    {"state": "banana", "detail": "bad"},
    {"state": 123, "detail": "bad"},
    {"state": "idle", "detail": 123},
    [],
    None,
])
def test_overlay_rejects_invalid_status_payload(payload):
    with pytest.raises(ValueError):
        overlay._parse_status_payload(payload)


class FakeResponse:
    def __init__(self, payload=None, error=None):
        self.payload = payload
        self.error = error

    def raise_for_status(self):
        if self.error:
            raise self.error

    def json(self):
        return self.payload


def test_overlay_fetch_rejects_http_error(monkeypatch):
    response = FakeResponse(error=overlay.requests.HTTPError("500"))
    monkeypatch.setattr(overlay.requests, "get", lambda *args, **kwargs: response)

    with pytest.raises(overlay.requests.HTTPError):
        overlay._fetch_status()


def test_overlay_fetch_accepts_valid_response(monkeypatch):
    response = FakeResponse(payload={"state": "idle", "detail": "ok"})
    monkeypatch.setattr(overlay.requests, "get", lambda *args, **kwargs: response)

    assert overlay._fetch_status() == ("idle", "ok")


def test_overlay_poll_status_sets_offline_on_network_error(monkeypatch, polling_bot):
    def fail():
        raise overlay.requests.ConnectionError("sidecar unavailable")

    monkeypatch.setattr(overlay, "_fetch_status", fail)

    overlay.RouterBot.poll_status(polling_bot)

    assert polling_bot.state == "offline"
    assert polling_bot.detail == "Không kết nối được 9router"
    assert polling_bot.tooltip == "OFFLINE — Không kết nối được 9router"
    assert polling_bot.updated is True


def test_overlay_poll_status_sets_offline_on_invalid_response(monkeypatch, polling_bot):
    monkeypatch.setattr(
        overlay,
        "_fetch_status",
        lambda: (_ for _ in ()).throw(ValueError("bad payload")),
    )

    overlay.RouterBot.poll_status(polling_bot)

    assert polling_bot.state == "offline"
    assert polling_bot.detail == "Phản hồi status không hợp lệ"
    assert polling_bot.tooltip == "OFFLINE — Phản hồi status không hợp lệ"
    assert polling_bot.updated is True


def test_overlay_poll_status_updates_valid_state(monkeypatch, polling_bot):
    monkeypatch.setattr(overlay, "_fetch_status", lambda: ("blocked", "all locked"))

    overlay.RouterBot.poll_status(polling_bot)

    assert polling_bot.state == "blocked"
    assert polling_bot.detail == "all locked"
    assert polling_bot.tooltip == "BLOCKED — all locked"
    assert polling_bot.updated is True
