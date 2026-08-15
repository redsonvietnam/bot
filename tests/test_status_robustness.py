import json
from datetime import datetime, timedelta, timezone

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
