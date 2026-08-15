from datetime import datetime, timedelta, timezone

from sidecar import app as sidecar_app
from tests.helpers import make_connections, write_db


def test_warning_when_at_least_half_active_connections_are_restricted(db_file):
    future = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    connections = make_connections()
    for connection in connections[:12]:
        connection["modelLock___all"] = future

    write_db(db_file, connections)

    result = sidecar_app._compute_status()

    assert result["state"] == "warning"
    assert result["detail"] == "12/23 connections dang bi han che"
