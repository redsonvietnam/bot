import pytest

from overlay import router_bot_overlay as overlay


class FakeResponse:
    def __init__(self, payload=None, *, status_error=None, json_error=None):
        self._payload = payload
        self._status_error = status_error
        self._json_error = json_error

    def raise_for_status(self):
        if self._status_error:
            raise self._status_error

    def json(self):
        if self._json_error:
            raise self._json_error
        return self._payload


def test_fetch_status_accepts_valid_payload(monkeypatch):
    response = FakeResponse({"state": "active", "detail": "ok"})
    monkeypatch.setattr(overlay.requests, "get", lambda *args, **kwargs: response)

    assert overlay._fetch_status() == ("active", "ok")


def test_fetch_status_raises_on_http_error(monkeypatch):
    error = overlay.requests.HTTPError("500")
    response = FakeResponse(status_error=error)
    monkeypatch.setattr(overlay.requests, "get", lambda *args, **kwargs: response)

    with pytest.raises(overlay.requests.RequestException):
        overlay._fetch_status()


def test_fetch_status_raises_on_malformed_json(monkeypatch):
    error = overlay.requests.exceptions.JSONDecodeError("bad json", "{", 0)
    response = FakeResponse(json_error=error)
    monkeypatch.setattr(overlay.requests, "get", lambda *args, **kwargs: response)

    with pytest.raises(overlay.requests.RequestException):
        overlay._fetch_status()


def test_fetch_status_rejects_unknown_state(monkeypatch):
    response = FakeResponse({"state": "unknown", "detail": "bad"})
    monkeypatch.setattr(overlay.requests, "get", lambda *args, **kwargs: response)

    with pytest.raises(ValueError):
        overlay._fetch_status()


def test_fetch_status_passes_timeout_to_requests(monkeypatch):
    response = FakeResponse({"state": "idle", "detail": "ok"})
    seen = {}

    def fake_get(url, **kwargs):
        seen["url"] = url
        seen.update(kwargs)
        return response

    monkeypatch.setattr(overlay.requests, "get", fake_get)

    assert overlay._fetch_status() == ("idle", "ok")
    assert seen["timeout"] == 2
