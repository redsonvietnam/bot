"""Lock 20/23 connections de test state 'blocked'. Tu tao backup truoc khi sua."""
import json
import os
import shutil
from datetime import datetime, timezone, timedelta

db_path = os.path.join(os.environ.get("APPDATA", ""), "9router", "db.json")
backup_path = db_path + ".bak"

# Tao backup TRUOC khi sua (chi tao neu chua co, tranh de backup bi ghi de
# boi trang thai da bi lock tu lan test truoc)
if not os.path.exists(backup_path):
    shutil.copy2(db_path, backup_path)
    print(f"Da tao backup: {backup_path}")
else:
    print(f"Backup da ton tai, giu nguyen: {backup_path}")

with open(db_path, "r", encoding="utf-8") as f:
    db = json.load(f)

now = datetime.now(timezone.utc)
future = (now + timedelta(minutes=10)).isoformat()

active = [c for c in db["providerConnections"] if c.get("isActive")]
locked = 0
for i, c in enumerate(active):
    if i < 20:
        c["modelLock___all"] = future
        locked += 1

with open(db_path, "w", encoding="utf-8") as f:
    json.dump(db, f, indent=2)

print(f"Da lock {locked}/{len(active)} connections cho test 'blocked'")
