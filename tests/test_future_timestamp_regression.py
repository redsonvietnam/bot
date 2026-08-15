from datetime import datetime, timedelta, timezone

from sidecar import app as sidecar_app
from tests.helpers import make_connections, write_db


def test_future_last_used_at_is_not_recent_in_api_status(db_file, monkeypatch):
    now = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)
    connections = make_connections(1)
    connections[0]["lastUsedAt"] = (now + timedelta(seconds=10)).isoformat()
    write_db(db_file, connections)
    monkeypatch.setattr(sidecar_app, "_now_utc", lambda: now)

    response = sidecar_app.app.test_client().get("/api/status")

    assert response.status_code == 200
    assert response.get_json() == {
        "state": "idle",
        "detail": "San sang - 1/1 connections kha dung",
    }
