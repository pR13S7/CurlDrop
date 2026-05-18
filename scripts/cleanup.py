#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/data/uploads"))
MAX_STORAGE = int(os.getenv("MAX_STORAGE", 1073741824))  # 1GB


def get_total_usage() -> int:
    return sum(f.stat().st_size for f in UPLOAD_DIR.glob("*.bin"))


def cleanup():
    if not UPLOAD_DIR.exists():
        return

    now = datetime.now(timezone.utc)
    deleted = 0

    # Delete expired files
    for meta_path in UPLOAD_DIR.glob("*.meta"):
        try:
            meta = json.loads(meta_path.read_text())
            expires_at = datetime.fromisoformat(meta["expires_at"])
            if now > expires_at:
                file_id = meta_path.stem
                meta_path.unlink(missing_ok=True)
                (UPLOAD_DIR / f"{file_id}.bin").unlink(missing_ok=True)
                deleted += 1
        except (json.JSONDecodeError, KeyError, ValueError):
            continue

    # Enforce storage limit — delete oldest first
    if get_total_usage() > MAX_STORAGE:
        files = []
        for meta_path in UPLOAD_DIR.glob("*.meta"):
            try:
                meta = json.loads(meta_path.read_text())
                files.append((meta.get("uploaded_at", ""), meta_path.stem))
            except (json.JSONDecodeError, KeyError):
                continue

        files.sort()
        for _, file_id in files:
            (UPLOAD_DIR / f"{file_id}.meta").unlink(missing_ok=True)
            (UPLOAD_DIR / f"{file_id}.bin").unlink(missing_ok=True)
            deleted += 1
            if get_total_usage() <= MAX_STORAGE:
                break

    if deleted:
        usage_mb = get_total_usage() / (1024 * 1024)
        print(f"[{now.isoformat()}] Cleaned up {deleted} file(s). Usage: {usage_mb:.1f} MB")


if __name__ == "__main__":
    cleanup()
