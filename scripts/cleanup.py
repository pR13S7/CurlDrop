#!/usr/bin/env python3
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

UPLOAD_DIR = Path("/data/uploads")


def cleanup():
    if not UPLOAD_DIR.exists():
        return

    now = datetime.now(timezone.utc)
    deleted = 0

    for meta_path in UPLOAD_DIR.glob("*.meta"):
        try:
            meta = json.loads(meta_path.read_text())
            expires_at = datetime.fromisoformat(meta["expires_at"])
            if now > expires_at:
                file_id = meta_path.stem
                meta_path.unlink(missing_ok=True)
                bin_path = UPLOAD_DIR / f"{file_id}.bin"
                bin_path.unlink(missing_ok=True)
                deleted += 1
        except (json.JSONDecodeError, KeyError, ValueError):
            continue

    if deleted:
        print(f"[{now.isoformat()}] Cleaned up {deleted} expired file(s)")


if __name__ == "__main__":
    cleanup()
