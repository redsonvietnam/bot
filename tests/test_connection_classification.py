from datetime import datetime, timedelta, timezone

import pytest

from sidecar import app as sidecar_app
from tests.helpers import make_connections, write_db


NOW = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)
RECENT = (NOW - timedelta(seconds=10)).isoformat()
BOUNDARY_RECENT = (NOW - timedelta(seconds=30)).isoformat()
STALE = (NOW - timedelta(seconds=31)).isoformat()
FUTURE = (NOW + timedelta(seconds=10)).isoformat()
ACTIVE_LOCK = (NOW + timedelta(minutes=5)).isoformat()
EXPIRED_LOCK = (NOW - timedelta(seconds=1)).isoformat()


def make_connection(**overrides):
    connection = {
        "isActive": True,
        "testStatus": "available",
        "lastUsedAt": None,
        "modelLock___all": None,
    }
    connection.update(overrides)
    return connection


def test_unavailable_connection_is_locked_and_not_recent():
    connection = make_connection(testStatus="unavailable", lastUsedAt=RECENT)

    assert sidecar_app._connection_status(connection, NOW) == ("locked", False)


def test_active_global_lock_is_locked_and_preserves_recent_flag():
    connection = make_connection(modelLock___all=ACTIVE_LOCK, lastUsedAt=RECENT)

    assert sidecar_app._connection_status(connection, NOW) == ("locked", True)


def test_expired_global_lock_does_not_lock_connection():
    connection = make_connection(modelLock___all=EXPIRED_LOCK, lastUsedAt=None)

    assert sidecar_app._connection_status(connection, NOW) == ("free", False)


@pytest.mark.parametrize(
    ("locks", "expected"),
    [
        ({"modelLock_a": None, "modelLock_b": None}, ("free", False)),
        ({"modelLock_a": ACTIVE_LOCK, "modelLock_b": EXPIRED_LOCK}, ("partial", False)),
        ({"modelLock_a": ACTIVE_LOCK, "modelLock_b": ACTIVE_LOCK}, ("locked", False)),
    ],
)
def test_per_model_lock_matrix(locks, expected):
    connection = make_connection(**locks)

    assert sidecar_app._connection_status(connection, NOW) == expected


def test_per_model_lock_matrix_preserves_recent_flag():
    connection = make_connection(
        lastUsedAt=RECENT,
        modelLock_a=ACTIVE_LOCK,
        modelLock_b=EXPIRED_LOCK,
    )

    assert sidecar_app._connection_status(connection, NOW) == ("partial", True)


def test_stale_last_used_at_is_not_recent_for_free_connection():
    connection = make_connection(lastUsedAt=STALE)

    assert sidecar_app._connection_status(connection, NOW) == ("free", False)


def test_exact_active_window_boundary_is_recent():
    connection = make_connection(lastUsedAt=BOUNDARY_RECENT)

    assert sidecar_app._connection_status(connection, NOW) == ("free", True)


def test_future_last_used_at_is_not_recent_for_free_connection():
    connection = make_connection(lastUsedAt=FUTURE)

    assert sidecar_app._connection_status(connection, NOW) == ("free", False)


def test_inactive_connections_are_excluded_from_aggregate_status(db_file, monkeypatch):
    connections = make_connections(2)
    connections[0]["isActive"] = False
    connections[1]["lastUsedAt"] = RECENT
    write_db(db_file, connections)
    monkeypatch.setattr(sidecar_app, "_now_utc", lambda: NOW)

    assert sidecar_app._compute_status() == {
        "state": "active",
        "detail": "Dang hoat dong - 1/1 connections kha dung",
    }


def test_unavailable_connection_counts_as_locked_in_aggregate_status(db_file, monkeypatch):
    connections = make_connections(2)
    connections[0]["testStatus"] = "unavailable"
    connections[1]["lastUsedAt"] = RECENT
    write_db(db_file, connections)
    monkeypatch.setattr(sidecar_app, "_now_utc", lambda: NOW)

    assert sidecar_app._compute_status() == {
        "state": "warning",
        "detail": "1/2 connections dang bi han che",
    }


def test_warning_threshold_at_fifty_percent_is_warning(db_file, monkeypatch):
    connections = make_connections(2)
    connections[0]["modelLock_a"] = ACTIVE_LOCK
    write_db(db_file, connections)
    monkeypatch.setattr(sidecar_app, "_now_utc", lambda: NOW)

    assert sidecar_app._compute_status() == {
        "state": "warning",
        "detail": "1/2 connections dang bi han che",
    }


def test_all_locked_is_blocked_at_and_above_warning_threshold(db_file, monkeypatch):
    connections = make_connections(2)
    for connection in connections:
        connection["modelLock_a"] = ACTIVE_LOCK
    write_db(db_file, connections)
    monkeypatch.setattr(sidecar_app, "_now_utc", lambda: NOW)

    assert sidecar_app._compute_status() == {
        "state": "blocked",
        "detail": "Tat ca 2 connections dang bi chan (rate-limit/cooldown)",
    }


def test_warning_threshold_just_below_fifty_percent_stays_active(db_file, monkeypatch):
    connections = make_connections(3)
    connections[0]["modelLock_a"] = ACTIVE_LOCK
    connections[1]["lastUsedAt"] = RECENT
    write_db(db_file, connections)
    monkeypatch.setattr(sidecar_app, "_now_utc", lambda: NOW)

    assert sidecar_app._compute_status() == {
        "state": "active",
        "detail": "Dang hoat dong - 2/3 connections kha dung",
    }


def test_warning_threshold_at_fifty_percent_is_warning_for_four_connections(db_file, monkeypatch):
    connections = make_connections(4)
    connections[0]["modelLock_a"] = ACTIVE_LOCK
    connections[1]["modelLock_a"] = ACTIVE_LOCK
    write_db(db_file, connections)
    monkeypatch.setattr(sidecar_app, "_now_utc", lambda: NOW)

    assert sidecar_app._compute_status() == {
        "state": "warning",
        "detail": "2/4 connections dang bi han che",
    }


def test_missing_test_status_is_treated_as_available_for_classification(db_file, monkeypatch):
    connection = make_connection(lastUsedAt=RECENT)
    del connection["testStatus"]
    write_db(db_file, [connection])
    monkeypatch.setattr(sidecar_app, "_now_utc", lambda: NOW)

    assert sidecar_app._compute_status() == {
        "state": "active",
        "detail": "Dang hoat dong - 1/1 connections kha dung",
    }


def test_missing_last_used_at_is_safe_and_not_recent(db_file, monkeypatch):
    connection = make_connection()
    del connection["lastUsedAt"]
    write_db(db_file, [connection])
    monkeypatch.setattr(sidecar_app, "_now_utc", lambda: NOW)

    assert sidecar_app._compute_status() == {
        "state": "idle",
        "detail": "San sang - 1/1 connections kha dung",
    }


def test_missing_model_lock_fields_is_safe_and_free(db_file, monkeypatch):
    connection = make_connection(lastUsedAt=RECENT)
    del connection["modelLock___all"]
    write_db(db_file, [connection])
    monkeypatch.setattr(sidecar_app, "_now_utc", lambda: NOW)

    assert sidecar_app._compute_status() == {
        "state": "active",
        "detail": "Dang hoat dong - 1/1 connections kha dung",
    }


def test_none_fields_are_treated_as_absent_values(db_file, monkeypatch):
    connection = make_connection(testStatus=None, lastUsedAt=None, modelLock___all=None)
    write_db(db_file, [connection])
    monkeypatch.setattr(sidecar_app, "_now_utc", lambda: NOW)

    assert sidecar_app._compute_status() == {
        "state": "idle",
        "detail": "San sang - 1/1 connections kha dung",
    }


def test_malformed_last_used_timestamp_is_safe_and_not_recent(db_file, monkeypatch):
    connection = make_connection(lastUsedAt="not-a-timestamp")
    write_db(db_file, [connection])
    monkeypatch.setattr(sidecar_app, "_now_utc", lambda: NOW)

    assert sidecar_app._compute_status() == {
        "state": "idle",
        "detail": "San sang - 1/1 connections kha dung",
    }


def test_malformed_lock_timestamp_is_ignored_while_valid_lock_remains_active():
    connection = make_connection(
        modelLock_a="not-a-timestamp",
        modelLock_b=ACTIVE_LOCK,
    )

    assert sidecar_app._connection_status(connection, NOW) == ("partial", False)


def test_mixed_valid_and_invalid_connection_fields_are_safe_in_aggregate(
    db_file, monkeypatch
):
    connections = [
        make_connection(lastUsedAt=RECENT),
        make_connection(lastUsedAt="not-a-timestamp"),
        make_connection(testStatus=None, lastUsedAt=None, modelLock___all=None),
    ]
    del connections[2]["modelLock___all"]
    write_db(db_file, connections)
    monkeypatch.setattr(sidecar_app, "_now_utc", lambda: NOW)

    assert sidecar_app._compute_status() == {
        "state": "active",
        "detail": "Dang hoat dong - 3/3 connections kha dung",
    }
