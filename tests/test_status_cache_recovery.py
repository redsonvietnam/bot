from sidecar import app as sidecar_app
from tests.helpers import make_connections, write_db


def _status(client):
    response = client.get("/api/status")
    assert response.status_code == 200
    assert response.is_json
    payload = response.get_json()
    assert isinstance(payload, dict)
    assert set(payload) == {"state", "detail"}
    return payload


def _valid_db(db_file, detail_connection_count=1):
    write_db(db_file, make_connections(detail_connection_count))


def test_initial_db_failure_returns_offline_default(db_file):
    client = sidecar_app.app.test_client()
    assert _status(client) == {
        "state": "offline",
        "detail": "Chua doc duoc du lieu",
    }


def test_valid_then_malformed_keeps_last_good(db_file, monkeypatch):
    _valid_db(db_file, 1)
    good = _status(sidecar_app.app.test_client())

    db_file.write_text("{broken", encoding="utf-8")
    monkeypatch.setattr(sidecar_app, "_last_good", good)

    assert _status(sidecar_app.app.test_client()) == good


def test_valid_then_missing_db_keeps_last_good(db_file):
    _valid_db(db_file, 1)
    client = sidecar_app.app.test_client()
    good = _status(client)

    db_file.unlink(missing_ok=True)

    assert _status(client) == good


def test_valid_then_invalid_root_keeps_last_good(db_file):
    _valid_db(db_file, 1)
    client = sidecar_app.app.test_client()
    good = _status(client)

    db_file.write_text("[]", encoding="utf-8")

    assert _status(client) == good


def test_failure_then_valid_db_recovers_and_replaces_cache(db_file):
    client = sidecar_app.app.test_client()
    assert _status(client) == {
        "state": "offline",
        "detail": "Chua doc duoc du lieu",
    }

    _valid_db(db_file, 1)
    recovered = _status(client)

    assert recovered["state"] == "idle"
    assert sidecar_app._last_good == recovered


def test_valid_a_then_failure_then_valid_b_returns_b(db_file):
    client = sidecar_app.app.test_client()
    _valid_db(db_file, 1)
    first = _status(client)

    db_file.write_text("{broken", encoding="utf-8")
    assert _status(client) == first

    _valid_db(db_file, 2)
    second = _status(client)

    assert second != first
    assert second["detail"] == "San sang - 2/2 connections kha dung"
    assert sidecar_app._last_good == second


def test_state_change_then_failure_does_not_revert_to_default(db_file):
    client = sidecar_app.app.test_client()
    _valid_db(db_file, 1)
    active_or_idle = _status(client)

    db_file.write_text("{broken", encoding="utf-8")
    assert _status(client) == active_or_idle
    assert _status(client) != {
        "state": "offline",
        "detail": "Chua doc duoc du lieu",
    }


def test_cache_isolated_between_tests_by_fixture(db_file):
    assert sidecar_app._last_good == {
        "state": "offline",
        "detail": "Chua doc duoc du lieu",
    }
