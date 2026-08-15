from sidecar import app as sidecar_app
from tests.helpers import make_connections, write_db


def test_idle_when_all_active_connections_are_free_and_not_recent(db_file):
    write_db(db_file, make_connections())

    assert sidecar_app._compute_status() == {
        "state": "idle",
        "detail": "San sang - 23/23 connections kha dung",
    }
