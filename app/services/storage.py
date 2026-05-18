from __future__ import annotations

import json
import secrets
import shutil
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

from app.config import UPLOAD_DIR, FILE_TTL_HOURS, ID_LENGTH, MAX_STORAGE


def generate_id() -> str:
    return secrets.token_urlsafe(ID_LENGTH)[:ID_LENGTH]


def get_meta_path(file_id: str) -> Path:
    return UPLOAD_DIR / f"{file_id}.meta"


def get_bin_path(file_id: str) -> Path:
    return UPLOAD_DIR / f"{file_id}.bin"


async def save_file(file_id: str, filename: str, content_type: str, file_obj) -> dict:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    bin_path = get_bin_path(file_id)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=UPLOAD_DIR)

    try:
        size = 0
        with open(tmp_fd, "wb") as tmp:
            while chunk := await file_obj.read(1024 * 1024):
                size += len(chunk)
                tmp.write(chunk)
        shutil.move(tmp_path, bin_path)
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise

    now = datetime.now(timezone.utc)
    meta = {
        "original_filename": filename,
        "content_type": content_type or "application/octet-stream",
        "size": size,
        "uploaded_at": now.isoformat(),
        "expires_at": (now + timedelta(hours=FILE_TTL_HOURS)).isoformat(),
    }
    get_meta_path(file_id).write_text(json.dumps(meta))
    return meta


def get_file_meta(file_id: str) -> dict | None:
    meta_path = get_meta_path(file_id)
    if not meta_path.exists():
        return None
    meta = json.loads(meta_path.read_text())
    expires_at = datetime.fromisoformat(meta["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        delete_file(file_id)
        return None
    return meta


def get_total_usage() -> int:
    if not UPLOAD_DIR.exists():
        return 0
    return sum(f.stat().st_size for f in UPLOAD_DIR.glob("*.bin"))


def enforce_storage_limit():
    """Delete oldest files until total usage is under MAX_STORAGE."""
    if get_total_usage() <= MAX_STORAGE:
        return

    files = []
    for meta_path in UPLOAD_DIR.glob("*.meta"):
        try:
            meta = json.loads(meta_path.read_text())
            files.append((meta.get("uploaded_at", ""), meta_path.stem))
        except (json.JSONDecodeError, KeyError):
            continue

    files.sort()
    for _, file_id in files:
        delete_file(file_id)
        if get_total_usage() <= MAX_STORAGE:
            break


def delete_file(file_id: str):
    get_meta_path(file_id).unlink(missing_ok=True)
    get_bin_path(file_id).unlink(missing_ok=True)
