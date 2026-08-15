import pytest

from sidecar import app as sidecar_app
from tests.helpers import make_polling_bot


@pytest.fixture
def db_file(tmp_path, monkeypatch):
    """Point the sidecar at an isolated temporary DB for each test."""
    path = tmp_path / "db.json"
    monkeypatch.setattr(sidecar_app, "DB_JSON_PATH", str(path))
    monkeypatch.setattr(
        sidecar_app,
        "_last_good",
        {"state": "offline", "detail": "Chua doc duoc du lieu"},
    )
    return path


@pytest.fixture
def polling_bot():
    """Provide a deterministic non-GUI double for overlay polling tests."""
    return make_polling_bot()
