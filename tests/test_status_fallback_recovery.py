import json

from sidecar import app as sidecar_app
from tests.helpers import make_connections, write_db


def test_api_status_preserves_last_good_state_when_db_becomes_malformed(db_file):
    connections = make_connections()
    connections[0]["testStatus"] = "unavailable"
    write_db(db_file, connections)
    expected = sidecar_app._compute_status()

    db_file.write_text('{"providerConnections": [', encoding="utf-8")

    response = sidecar_app.app.test_client().get("/api/status")

    assert response.status_code == 200
    assert response.get_json() == expected


def test_api_status_preserves_last_good_state_when_db_becomes_unavailable(db_file):
    connections = make_connections()
    connections[0]["testStatus"] = "unavailable"
    write_db(db_file, connections)
    expected = sidecar_app._compute_status()

    db_file.unlink()

    response = sidecar_app.app.test_client().get("/api/status")

    assert response.status_code == 200
    assert response.get_json() == expected


def test_api_status_preserves_last_good_state_after_invalid_db_root(db_file):
    connections = make_connections()
    connections[0]["testStatus"] = "unavailable"
    write_db(db_file, connections)
    expected = sidecar_app._compute_status()

    db_file.write_text(json.dumps([]), encoding="utf-8")

    response = sidecar_app.app.test_client().get("/api/status")

    assert response.status_code == 200
    assert response.get_json() == expected


def test_api_status_recovers_from_cached_failure_to_new_valid_state(db_file):
    connections = make_connections()
    connections[0]["testStatus"] = "unavailable"
    write_db(db_file, connections)
    expected_before_failure = sidecar_app._compute_status()

    db_file.write_text("{malformed", encoding="utf-8")
    failed_response = sidecar_app.app.test_client().get("/api/status")

    assert failed_response.status_code == 200
    assert failed_response.get_json() == expected_before_failure

    recovered_connections = make_connections()
    recovered_connections[0]["testStatus"] = "available"
    recovered_connections[0]["lastUsedAt"] = None
    write_db(db_file, recovered_connections)

    recovered_response = sidecar_app.app.test_client().get("/api/status")

    assert recovered_response.status_code == 200
    assert recovered_response.get_json() == {
        "state": "idle",
        "detail": "San sang - 23/23 connections kha dung",
    }
