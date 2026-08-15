from datetime import datetime, timedelta, timezone

from sidecar import app as sidecar_app
from tests.helpers import make_connections, write_db


def test_blocked_when_all_active_connections_are_locked(db_file):
    future = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    connections = make_connections()
    for connection in connections:
        connection["modelLock___all"] = future

    write_db(db_file, connections)

    assert sidecar_app._compute_status() == {
        "state": "blocked",
        "detail": "Tat ca 23 connections dang bi chan (rate-limit/cooldown)",
    }
