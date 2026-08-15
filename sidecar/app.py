"""
9router Status Sidecar - Flask app phuc vu GET /api/status cho bot overlay.

Doc truc tiep db.json cua 9router, tinh trang thai dua tren modelLock timestamps
va testStatus. Khong goi API 9router, khong sua du lieu.

Chay:  python app.py
Test:  curl http://127.0.0.1:5000/api/status
"""

import json
import os
import sys
import logging
from datetime import datetime, timezone
from flask import Flask, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.WARNING)
log = logging.getLogger("9router-sidecar")

# -- Config --
DB_JSON_PATH = os.path.join(
    os.environ.get("APPDATA") or os.path.expanduser("~"),
    "9router", "db.json",
)
ACTIVE_WINDOW_SEC = 30
WARNING_LOCKED_RATIO = 0.5
MODEL_LOCK_PREFIX = "modelLock_"

# -- Cache last-good-state --
_last_good = {"state": "idle", "detail": "Chua doc duoc du lieu"}


def _now_utc():
    return datetime.now(timezone.utc)


def _parse_iso(s):
    if not s:
        return None
    try:
        s = str(s).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _is_recent(conn, now):
    dt = _parse_iso(conn.get("lastUsedAt"))
    if not dt:
        return False
    return (now - dt).total_seconds() <= ACTIVE_WINDOW_SEC


def _connection_status(conn, now):
    if conn.get("testStatus") == "unavailable":
        return "locked", False

    lock_fields = {
        k: v for k, v in conn.items()
        if k.startswith(MODEL_LOCK_PREFIX)
    }

    all_lock = _parse_iso(lock_fields.get("modelLock___all"))
    if all_lock and all_lock > now:
        return "locked", _is_recent(conn, now)

    per_model = {k: v for k, v in lock_fields.items() if k != "modelLock___all"}
    if not per_model:
        return "free", _is_recent(conn, now)

    active_locks = 0
    for k, v in per_model.items():
        dt = _parse_iso(v)
        if dt and dt > now:
            active_locks += 1

    recent = _is_recent(conn, now)
    if active_locks == 0:
        return "free", recent
    if active_locks == len(per_model):
        return "locked", recent
    return "partial", recent


def _compute_status():
    global _last_good

    with open(DB_JSON_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)

    connections = db.get("providerConnections")
    if not connections or not isinstance(connections, list):
        log.warning("providerConnections missing or empty in db.json")
        result = {"state": "idle", "detail": "Khong co connection nao duoc cau hinh"}
        _last_good = result
        return result

    active_conns = [c for c in connections if c.get("isActive")]
    if not active_conns:
        # Day la user chu dong tat het connection, khong phai bi rate-limit
        # that -> khong nen to mau do (blocked) giong het truong hop bi chan
        # that su, de tranh bao dong gia.
        result = {"state": "idle", "detail": "Tat ca connections deu bi tat (chu dong)"}
        _last_good = result
        return result

    now = _now_utc()
    total = len(active_conns)
    free_count = 0
    locked_count = 0
    partial_count = 0
    any_recent = False
    # ponytail: chi dem locked/partial/free, khong track per-provider.
    # Nang cap: group by provider neu can detail chi tiet hon.

    missing_expected_fields = False
    missing_field_names = set()
    for conn in active_conns:
        if "testStatus" not in conn:
            missing_expected_fields = True
            missing_field_names.add("testStatus")
        if "lastUsedAt" not in conn:
            missing_expected_fields = True
            missing_field_names.add("lastUsedAt")
        if not any(k.startswith(MODEL_LOCK_PREFIX) for k in conn.keys()):
            missing_expected_fields = True
            missing_field_names.add(f"{MODEL_LOCK_PREFIX}*")

        status, recent = _connection_status(conn, now)
        if status == "free":
            free_count += 1
        elif status == "locked":
            locked_count += 1
        else:
            partial_count += 1
        if recent:
            any_recent = True

    if missing_expected_fields:
        log.warning(
            "Mot so connection thieu field mong doi (%s) - "
            "co the 9router da thay doi cau truc db.json, "
            "state tra ve co the khong chinh xac",
            ", ".join(sorted(missing_field_names)),
        )

    not_free = locked_count + partial_count

    if free_count == 0 and partial_count == 0:
        state = "blocked"
        detail = f"Tat ca {total} connections dang bi chan (rate-limit/cooldown)"
    elif not_free / total >= WARNING_LOCKED_RATIO:
        state = "warning"
        detail = f"{not_free}/{total} connections dang bi han che"
    elif any_recent:
        state = "active"
        detail = f"Dang hoat dong - {free_count}/{total} connections kha dung"
    else:
        state = "idle"
        detail = f"San sang - {free_count}/{total} connections kha dung"

    result = {"state": state, "detail": detail}
    _last_good = result
    return result


@app.route("/api/status")
def api_status():
    try:
        result = _compute_status()
    except Exception as e:
        log.warning("Doc db.json loi, tra cache: %s", e)
        result = _last_good
    return jsonify(result)


if __name__ == "__main__":
    if not os.path.exists(DB_JSON_PATH):
        print(f"Khong tim thay {DB_JSON_PATH}", file=sys.stderr)
        print("   Dam bao 9router da chay it nhat 1 lan.", file=sys.stderr)
        sys.exit(1)
    print(f"Doc db.json tu: {DB_JSON_PATH}")
    print(f"Sidecar dang chay: http://127.0.0.1:5000/api/status")
    app.run(host="127.0.0.1", port=5000, debug=False)