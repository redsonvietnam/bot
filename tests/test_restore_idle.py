"""Restore db.json ve trang thai goc (idle) va xoa file backup."""
import os
import shutil

db_path = os.path.join(os.environ.get("APPDATA", ""), "9router", "db.json")
backup_path = db_path + ".bak"

if not os.path.exists(backup_path):
    raise SystemExit(f"Khong tim thay backup {backup_path} - khong co gi de restore")

shutil.copy2(backup_path, db_path)
print("Da restore db.json ve trang thai goc")

os.remove(backup_path)
print("Da xoa file backup")
