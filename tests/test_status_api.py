import json
from datetime import datetime, timedelta, timezone

from sidecar import app as sidecar_app
from tests.helpers import make_connections, write_db


NOW = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)
RECENT = (NOW - timedelta(seconds=10)).isoformat()
ACTIVE_LOCK = (NOW + timedelta(minutes=5)).isoformat()


def test_api_status_returns_200_and_valid_json_contract(db_file, monkeypatch):
    write_db(db_file, [make_connections(1)[0] | {"lastUsedAt": RECENT}])
    monkeypatch.setattr(sidecar_app, "_now_utc", lambda: NOW)

    response = sidecar_app.app.test_client().get("/api/status")

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == {
        "state": "active",
        "detail": "Dang hoat dong - 1/1 connections kha dung",
    }
    assert set(response.get_json()) == {"state", "detail"}


def test_api_status_returns_last_good_when_db_json_is_malformed(db_file):
    db_file.write_text("{not valid json", encoding="utf-8")
    sidecar_app._last_good = {
        "state": "active",
        "detail": "cached status",
    }

    response = sidecar_app.app.test_client().get("/api/status")

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == {
        "state": "active",
        "detail": "cached status",
    }


def test_api_status_returns_last_good_when_db_is_unavailable(db_file):
    db_file.unlink()
    sidecar_app._last_good = {
        "state": "warning",
        "detail": "cached warning",
    }

    response = sidecar_app.app.test_client().get("/api/status")

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == {
        "state": "warning",
        "detail": "cached warning",
    }


def test_api_status_returns_last_good_for_invalid_db_root(db_file):
    db_file.write_text(json.dumps([]), encoding="utf-8")
    sidecar_app._last_good = {
        "state": "blocked",
        "detail": "cached blocked",
    }

    response = sidecar_app.app.test_client().get("/api/status")

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == {
        "state": "blocked",
        "detail": "cached blocked",
    }


def test_api_status_recovers_after_invalid_db_then_valid_db(db_file, monkeypatch):
    sidecar_app._last_good = {
        "state": "offline",
        "detail": "Chua doc duoc du lieu",
    }
    db_file.write_text("{broken", encoding="utf-8")

    first = sidecar_app.app.test_client().get("/api/status")

    assert first.status_code == 200
    assert first.get_json() == {
        "state": "offline",
        "detail": "Chua doc duoc du lieu",
    }

    write_db(db_file, [make_connections(1)[0] | {"lastUsedAt": RECENT}])
    monkeypatch.setattr(sidecar_app, "_now_utc", lambda: NOW)

    recovered = sidecar_app.app.test_client().get("/api/status")

    assert recovered.status_code == 200
    assert recovered.get_json() == {
        "state": "active",
        "detail": "Dang hoat dong - 1/1 connections kha dung",
    }
    assert sidecar_app._last_good == recovered.get_json()


def test_api_status_recovers_from_unavailable_db_to_valid_status(db_file, monkeypatch):
    sidecar_app._last_good = {
        "state": "warning",
        "detail": "cached warning",
    }

    first = sidecar_app.app.test_client().get("/api/status")

    assert first.status_code == 200
    assert first.get_json() == {
        "state": "warning",
        "detail": "cached warning",
    }

    write_db(db_file, [make_connections(1)[0] | {"lastUsedAt": RECENT}])
    monkeypatch.setattr(sidecar_app, "_now_utc", lambda: NOW)

    recovered = sidecar_app.app.test_client().get("/api/status")

    assert recovered.status_code == 200
    assert recovered.get_json() == {
        "state": "active",
        "detail": "Dang hoat dong - 1/1 connections kha dung",
    }


def test_api_status_preserves_blocked_state_contract(db_file, monkeypatch):
    connections = make_connections(2)
    for connection in connections:
        connection["modelLock_a"] = ACTIVE_LOCK
    write_db(db_file, connections)
    monkeypatch.setattr(sidecar_app, "_now_utc", lambda: NOW)

    response = sidecar_app.app.test_client().get("/api/status")

    assert response.status_code == 200
    assert response.get_json() == {
        "state": "blocked",
        "detail": "Tat ca 2 connections dang bi chan (rate-limit/cooldown)",
    }


def test_api_status_preserves_warning_state_contract(db_file, monkeypatch):
    connections = make_connections(2)
    connections[0]["modelLock_a"] = ACTIVE_LOCK
    write_db(db_file, connections)
    monkeypatch.setattr(sidecar_app, "_now_utc", lambda: NOW)

    response = sidecar_app.app.test_client().get("/api/status")

    assert response.status_code == 200
    assert response.get_json() == {
        "state": "warning",
        "detail": "1/2 connections dang bi han che",
    }


def test_api_status_preserves_idle_state_contract(db_file, monkeypatch):
    write_db(db_file, make_connections(2))
    monkeypatch.setattr(sidecar_app, "_now_utc", lambda: NOW)

    response = sidecar_app.app.test_client().get("/api/status")

    assert response.status_code == 200
    assert response.get_json() == {
        "state": "idle",
        "detail": "San sang - 2/2 connections kha dung",
    }
