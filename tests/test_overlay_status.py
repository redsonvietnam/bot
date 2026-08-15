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


def test_fetch_status_raises_on_connection_error(monkeypatch):
    error = overlay.requests.ConnectionError("sidecar unavailable")
    monkeypatch.setattr(overlay.requests, "get", lambda *args, **kwargs: (_ for _ in ()).throw(error))

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


def test_poll_status_active_then_connection_failure_sets_offline(monkeypatch, polling_bot):
    responses = iter([
        FakeResponse({"state": "active", "detail": "working"}),
    ])
    error = overlay.requests.ConnectionError("sidecar unavailable")

    def fake_get(*args, **kwargs):
        try:
            return next(responses)
        except StopIteration:
            raise error

    monkeypatch.setattr(overlay.requests, "get", fake_get)

    polling_bot.poll_status = overlay.RouterBot.poll_status.__get__(polling_bot)
    polling_bot.poll_status()
    assert (polling_bot.state, polling_bot.detail) == ("active", "working")

    polling_bot.poll_status()
    assert (polling_bot.state, polling_bot.detail) == (
        "offline",
        "Không kết nối được 9router",
    )


def test_poll_status_warning_then_http_500_sets_offline(monkeypatch, polling_bot):
    responses = iter([
        FakeResponse({"state": "warning", "detail": "limited"}),
        FakeResponse(status_error=overlay.requests.HTTPError("500")),
    ])
    monkeypatch.setattr(overlay.requests, "get", lambda *args, **kwargs: next(responses))

    polling_bot.poll_status = overlay.RouterBot.poll_status.__get__(polling_bot)
    polling_bot.poll_status()
    assert (polling_bot.state, polling_bot.detail) == ("warning", "limited")

    polling_bot.poll_status()
    assert (polling_bot.state, polling_bot.detail) == (
        "offline",
        "Không kết nối được 9router",
    )


def test_poll_status_blocked_then_malformed_json_sets_offline(monkeypatch, polling_bot):
    malformed = overlay.requests.exceptions.JSONDecodeError("bad json", "{", 0)
    responses = iter([
        FakeResponse({"state": "blocked", "detail": "cooldown"}),
        FakeResponse(json_error=malformed),
    ])
    monkeypatch.setattr(overlay.requests, "get", lambda *args, **kwargs: next(responses))

    polling_bot.poll_status = overlay.RouterBot.poll_status.__get__(polling_bot)
    polling_bot.poll_status()
    assert (polling_bot.state, polling_bot.detail) == ("blocked", "cooldown")

    polling_bot.poll_status()
    assert (polling_bot.state, polling_bot.detail) == (
        "offline",
        "Không kết nối được 9router",
    )


def test_poll_status_offline_recovers_to_active(monkeypatch, polling_bot):
    error = overlay.requests.ConnectionError("sidecar unavailable")
    responses = iter([
        error,
        FakeResponse({"state": "active", "detail": "recovered"}),
    ])

    def fake_get(*args, **kwargs):
        outcome = next(responses)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(overlay.requests, "get", fake_get)

    polling_bot.poll_status = overlay.RouterBot.poll_status.__get__(polling_bot)
    polling_bot.poll_status()
    assert (polling_bot.state, polling_bot.detail) == (
        "offline",
        "Không kết nối được 9router",
    )

    polling_bot.poll_status()
    assert (polling_bot.state, polling_bot.detail) == ("active", "recovered")


def test_poll_status_offline_recovers_to_idle(monkeypatch, polling_bot):
    error = overlay.requests.ConnectionError("sidecar unavailable")
    responses = iter([
        error,
        FakeResponse({"state": "idle", "detail": "ready"}),
    ])

    def fake_get(*args, **kwargs):
        outcome = next(responses)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(overlay.requests, "get", fake_get)

    polling_bot.poll_status = overlay.RouterBot.poll_status.__get__(polling_bot)
    polling_bot.poll_status()
    assert (polling_bot.state, polling_bot.detail) == (
        "offline",
        "Không kết nối được 9router",
    )

    polling_bot.poll_status()
    assert (polling_bot.state, polling_bot.detail) == ("idle", "ready")


@pytest.mark.parametrize(
    "payload",
    [
        {"state": "unknown", "detail": "bad"},
        {"state": "active", "detail": 123},
    ],
)
def test_poll_status_invalid_payload_sets_offline(monkeypatch, polling_bot, payload):
    response = FakeResponse(payload)
    monkeypatch.setattr(overlay.requests, "get", lambda *args, **kwargs: response)

    polling_bot.poll_status = overlay.RouterBot.poll_status.__get__(polling_bot)
    polling_bot.poll_status()

    assert (polling_bot.state, polling_bot.detail) == (
        "offline",
        "Phản hồi status không hợp lệ",
    )


def test_poll_status_repeated_request_failures_keep_polling_path_alive(monkeypatch, polling_bot):
    error = overlay.requests.ConnectionError("sidecar unavailable")
    monkeypatch.setattr(
        overlay.requests,
        "get",
        lambda *args, **kwargs: (_ for _ in ()).throw(error),
    )

    polling_bot.poll_status = overlay.RouterBot.poll_status.__get__(polling_bot)
    for _ in range(3):
        polling_bot.poll_status()
        assert (polling_bot.state, polling_bot.detail) == (
            "offline",
            "Không kết nối được 9router",
        )


def test_poll_status_valid_state_replaces_stale_offline_state(monkeypatch, polling_bot):
    error = overlay.requests.ConnectionError("sidecar unavailable")
    responses = iter([
        error,
        FakeResponse({"state": "warning", "detail": "limited"}),
    ])

    def fake_get(*args, **kwargs):
        outcome = next(responses)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(overlay.requests, "get", fake_get)

    polling_bot.poll_status = overlay.RouterBot.poll_status.__get__(polling_bot)
    polling_bot.poll_status()
    assert (polling_bot.state, polling_bot.detail) == (
        "offline",
        "Không kết nối được 9router",
    )

    polling_bot.poll_status()
    assert (polling_bot.state, polling_bot.detail) == ("warning", "limited")
