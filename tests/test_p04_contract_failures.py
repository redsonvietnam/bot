import json

import pytest
from flask import Response, jsonify

from overlay import router_bot_overlay as overlay
from tests.test_p04_real_contract import sidecar_client, _wire_sidecar_to_overlay
from sidecar import app as sidecar_app


def test_sidecar_http_500_becomes_overlay_request_failure(
    monkeypatch, sidecar_client
):
    def failing_status():
        return jsonify({"state": "offline", "detail": "sidecar failure"}), 500

    monkeypatch.setitem(
        sidecar_app.app.view_functions, "api_status", failing_status
    )
    _wire_sidecar_to_overlay(monkeypatch, sidecar_client)

    with pytest.raises(Exception) as exc_info:
        overlay._fetch_status()

    assert exc_info.value.response is not None
    assert exc_info.value.response.status_code == 500


def test_sidecar_malformed_json_becomes_overlay_contract_failure(
    monkeypatch, sidecar_client
):
    def malformed_status():
        return Response("{not-json", status=200, content_type="application/json")

    monkeypatch.setitem(
        sidecar_app.app.view_functions, "api_status", malformed_status
    )
    _wire_sidecar_to_overlay(monkeypatch, sidecar_client)

    with pytest.raises(ValueError, match="status response must be an object"):
        overlay._fetch_status()


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"state": "not-a-state", "detail": "bad state"}, "unknown state"),
        ({"state": "active", "detail": 123}, "invalid detail"),
    ],
)
def test_sidecar_invalid_contract_is_rejected_by_overlay(
    monkeypatch, sidecar_client, payload, message
):
    monkeypatch.setattr(sidecar_app, "_compute_status", lambda: payload)
    _wire_sidecar_to_overlay(monkeypatch, sidecar_client)

    with pytest.raises(ValueError, match=message):
        overlay._fetch_status()


def test_sidecar_failure_then_valid_response_recovers_to_new_state(
    monkeypatch, sidecar_client, tmp_path
):
    cached = {"state": "warning", "detail": "cached warning"}
    monkeypatch.setattr(sidecar_app, "_last_good", cached)
    _wire_sidecar_to_overlay(monkeypatch, sidecar_client)

    first = overlay._fetch_status()
    assert first == ("warning", "cached warning")

    db = {
        "providerConnections": [
            {
                "isActive": True,
                "testStatus": "available",
                "lastUsedAt": "2026-08-16T00:00:00+00:00",
                "modelLock___all": None,
            }
        ]
    }
    (tmp_path / "db.json").write_text(json.dumps(db), encoding="utf-8")
    monkeypatch.setattr(
        sidecar_app, "_now_utc", lambda: __import__("datetime").datetime.fromisoformat(
            "2026-08-16T00:00:10+00:00"
        )
    )

    second = overlay._fetch_status()
    assert second == (
        "active",
        "Dang hoat dong - 1/1 connections kha dung",
    )
    assert second != first
