"""Restore db.json ve trang thai goc, roi lock 12/23 connections de test 'warning'."""
import json
import os
import shutil
from datetime import datetime, timezone, timedelta

db_path = os.path.join(os.environ.get("APPDATA", ""), "9router", "db.json")
backup_path = db_path + ".bak"

if not os.path.exists(backup_path):
    raise SystemExit(f"Khong tim thay backup {backup_path} - chay test_blocked.py truoc")

# Restore ve trang thai goc (KHONG xoa backup, con dung tiep cho buoc idle)
shutil.copy2(backup_path, db_path)
print("Da restore db.json tu backup")

with open(db_path, "r", encoding="utf-8") as f:
    db = json.load(f)

now = datetime.now(timezone.utc)
future = (now + timedelta(minutes=10)).isoformat()

active = [c for c in db["providerConnections"] if c.get("isActive")]
locked = 0
for i, c in enumerate(active):
    if i < 12:
        c["modelLock___all"] = future
        locked += 1

with open(db_path, "w", encoding="utf-8") as f:
    json.dump(db, f, indent=2)

print(f"Da lock {locked}/{len(active)} connections cho test 'warning'")
