import json

import pytest

from sidecar import app as sidecar_app
from tests.helpers import make_connections, write_db


VALID_STATES = ("idle", "active", "warning", "blocked", "offline")


def _get_status():
    return sidecar_app.app.test_client().get("/api/status")


@pytest.mark.parametrize("state", VALID_STATES)
def test_api_status_fallback_state_is_contract_valid(db_file, state):
    db_file.write_text("{broken", encoding="utf-8")
    sidecar_app._last_good = {
        "state": state,
        "detail": f"cached {state}",
    }

    response = _get_status()
    payload = response.get_json()

    assert response.status_code == 200
    assert response.is_json
    assert isinstance(payload, dict)
    assert set(payload) == {"state", "detail"}
    assert payload["state"] in VALID_STATES
    assert payload["state"] == state
    assert isinstance(payload["detail"], str)


def test_api_status_invalid_root_preserves_object_contract(db_file):
    db_file.write_text(json.dumps([]), encoding="utf-8")
    sidecar_app._last_good = {
        "state": "offline",
        "detail": "cached offline",
    }

    response = _get_status()
    payload = response.get_json()

    assert response.status_code == 200
    assert response.is_json
    assert isinstance(payload, dict)
    assert set(payload) == {"state", "detail"}
    assert payload == {
        "state": "offline",
        "detail": "cached offline",
    }


def test_api_status_valid_db_response_is_object_contract(db_file, monkeypatch):
    write_db(db_file, make_connections(1))
    monkeypatch.setattr(sidecar_app, "_now_utc", sidecar_app._now_utc)

    response = _get_status()
    payload = response.get_json()

    assert response.status_code == 200
    assert response.is_json
    assert isinstance(payload, dict)
    assert set(payload) == {"state", "detail"}
    assert payload["state"] in VALID_STATES
    assert isinstance(payload["detail"], str)


def test_api_status_failure_then_recovery_returns_new_valid_contract(db_file, monkeypatch):
    sidecar_app._last_good = {
        "state": "offline",
        "detail": "cached offline",
    }
    db_file.write_text("{broken", encoding="utf-8")

    failed = _get_status()
    assert failed.status_code == 200
    assert failed.get_json() == sidecar_app._last_good

    write_db(db_file, make_connections(1))
    monkeypatch.setattr(sidecar_app, "_now_utc", sidecar_app._now_utc)

    recovered = _get_status()
    payload = recovered.get_json()

    assert recovered.status_code == 200
    assert recovered.is_json
    assert isinstance(payload, dict)
    assert set(payload) == {"state", "detail"}
    assert payload["state"] in VALID_STATES
    assert isinstance(payload["detail"], str)
    assert payload["state"] != "offline"
