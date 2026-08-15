import pytest

from sidecar import app as sidecar_app


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
