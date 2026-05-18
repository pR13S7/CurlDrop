import os
import re

from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import BASE_URL, MAX_FILE_SIZE, MAX_STORAGE
from app.services.storage import generate_id, save_file, get_bin_path, get_total_usage, enforce_storage_limit

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def sanitize_filename(filename: str) -> str:
    name = os.path.basename(filename)
    name = re.sub(r'[^\w\s\-.]', '', name)
    return name[:255] or "upload"


@router.post("/api/upload")
@limiter.limit("10/minute")
async def upload_file(request: Request, file: UploadFile = File(...)):
    filename = sanitize_filename(file.filename or "upload")

    file_id = generate_id()
    while get_bin_path(file_id).exists():
        file_id = generate_id()

    if get_total_usage() >= MAX_STORAGE:
        enforce_storage_limit()
        if get_total_usage() >= MAX_STORAGE:
            raise HTTPException(status_code=507, detail="Storage full. Try again later.")

    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 200MB.")

    meta = await save_file(file_id, filename, file.content_type, file)

    if meta["size"] > MAX_FILE_SIZE:
        from app.services.storage import delete_file
        delete_file(file_id)
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 200MB.")

    download_url = f"{BASE_URL}/d/{file_id}"

    return {
        "id": file_id,
        "filename": meta["original_filename"],
        "size": meta["size"],
        "expires_at": meta["expires_at"],
        "download_url": download_url,
        "curl_command": f"curl -OJ {download_url}",
        "wget_command": f"wget --content-disposition {download_url}",
    }
