import os

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


@pytest.mark.parametrize(
    "state,detail",
    [
        ("idle", "ready"),
        ("active", "working"),
        ("warning", "limited"),
        ("blocked", "cooldown"),
        ("offline", "unavailable"),
    ],
)
def test_sidecar_overlay_state_detail_contract(monkeypatch, state, detail):
    payload = {"state": state, "detail": detail}
    monkeypatch.setattr(
        overlay.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(payload),
    )

    assert overlay._fetch_status() == (state, detail)


def test_overlay_maps_sidecar_http_failure_to_offline(monkeypatch, polling_bot):
    response = FakeResponse(status_error=overlay.requests.HTTPError("500"))
    monkeypatch.setattr(overlay.requests, "get", lambda *args, **kwargs: response)

    polling_bot.poll_status = overlay.RouterBot.poll_status.__get__(polling_bot)
    polling_bot.poll_status()

    assert (polling_bot.state, polling_bot.detail) == (
        "offline",
        "Không kết nối được 9router",
    )


def test_overlay_maps_sidecar_unavailable_to_offline(monkeypatch, polling_bot):
    error = overlay.requests.ConnectionError("sidecar unavailable")
    monkeypatch.setattr(
        overlay.requests,
        "get",
        lambda *args, **kwargs: (_ for _ in ()).throw(error),
    )

    polling_bot.poll_status = overlay.RouterBot.poll_status.__get__(polling_bot)
    polling_bot.poll_status()

    assert (polling_bot.state, polling_bot.detail) == (
        "offline",
        "Không kết nối được 9router",
    )


def test_overlay_maps_malformed_json_to_invalid_offline(monkeypatch, polling_bot):
    error = overlay.requests.exceptions.JSONDecodeError("bad json", "{", 0)
    response = FakeResponse(json_error=error)
    monkeypatch.setattr(overlay.requests, "get", lambda *args, **kwargs: response)

    polling_bot.poll_status = overlay.RouterBot.poll_status.__get__(polling_bot)
    polling_bot.poll_status()

    assert (polling_bot.state, polling_bot.detail) == (
        "offline",
        "Không kết nối được 9router",
    )


def test_overlay_recovers_from_sidecar_unavailable_to_valid_state(monkeypatch, polling_bot):
    outcomes = [
        overlay.requests.ConnectionError("sidecar unavailable"),
        FakeResponse({"state": "active", "detail": "recovered"}),
    ]

    def fake_get(*args, **kwargs):
        outcome = outcomes.pop(0)
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


def test_overlay_accepts_valid_state_with_timestamp_metadata(monkeypatch, polling_bot):
    payload = {
        "state": "warning",
        "detail": "limited",
        "timestamp": 9999999999,
    }
    monkeypatch.setattr(
        overlay.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(payload),
    )

    polling_bot.poll_status = overlay.RouterBot.poll_status.__get__(polling_bot)
    polling_bot.poll_status()

    assert (polling_bot.state, polling_bot.detail) == ("warning", "limited")


def test_overlay_replaces_state_when_timestamp_metadata_changes(monkeypatch, polling_bot):
    payloads = iter([
        {"state": "warning", "detail": "stale" , "timestamp": 1},
        {"state": "idle", "detail": "fresh", "timestamp": 9999999999},
    ])
    monkeypatch.setattr(
        overlay.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(next(payloads)),
    )

    polling_bot.poll_status = overlay.RouterBot.poll_status.__get__(polling_bot)
    polling_bot.poll_status()
    assert (polling_bot.state, polling_bot.detail) == ("warning", "stale")

    polling_bot.poll_status()
    assert (polling_bot.state, polling_bot.detail) == ("idle", "fresh")


@pytest.fixture(scope="module")
def p04_qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app
    app.processEvents()


def _make_headless_bot(monkeypatch):
    monkeypatch.setattr(overlay.RouterBot, "_setup_window", lambda self: None)
    monkeypatch.setattr(overlay.RouterBot, "_restore_position", lambda self: None)
    monkeypatch.setattr(overlay, "_fetch_status", lambda: ("idle", "ready"))
    return overlay.RouterBot()


def test_sidecar_failure_does_not_replace_poll_timer(monkeypatch, p04_qapp):
    error = overlay.requests.ConnectionError("sidecar unavailable")
    monkeypatch.setattr(overlay, "_fetch_status", lambda: (_ for _ in ()).throw(error))
    bot = _make_headless_bot(monkeypatch)
    poll_timer = bot.poll_timer

    bot.poll_status()
    bot.poll_status()

    assert (bot.state, bot.detail) == (
        "offline",
        "Không kết nối được 9router",
    )
    assert bot.poll_timer is poll_timer
    assert bot.poll_timer.isActive()

    bot.close()


def test_close_stops_polling_timer_without_changing_last_state(monkeypatch, p04_qapp):
    monkeypatch.setattr(overlay, "_fetch_status", lambda: ("active", "working"))
    bot = _make_headless_bot(monkeypatch)

    bot.poll_status()
    assert (bot.state, bot.detail) == ("active", "working")
    assert bot.poll_timer.isActive()

    bot.close()

    assert not bot.poll_timer.isActive()
    assert (bot.state, bot.detail) == ("active", "working")
    bot.deleteLater()
