import re
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse

from app.config import BASE_URL
from app.services.storage import get_file_meta, get_bin_path

router = APIRouter()

VALID_ID = re.compile(r'^[a-zA-Z0-9_-]+$')


def is_browser(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "text/html" in accept


@router.get("/d/{file_id}")
async def download_file(file_id: str, request: Request):
    if not VALID_ID.match(file_id):
        raise HTTPException(status_code=400, detail="Invalid file ID")

    meta = get_file_meta(file_id)
    if meta is None:
        if is_browser(request):
            return HTMLResponse(
                content="<h1>File expired or not found</h1><p>This file has been deleted or never existed.</p>",
                status_code=410,
            )
        return PlainTextResponse("File expired or not found", status_code=410)

    bin_path = get_bin_path(file_id)
    if not bin_path.exists():
        raise HTTPException(status_code=410, detail="File expired or not found")

    if is_browser(request):
        download_url = f"{BASE_URL}/d/{file_id}"
        filename = meta["original_filename"]
        size_mb = meta["size"] / (1024 * 1024)
        return HTMLResponse(content=f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Download {filename}</title>
<script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-gray-900 text-white min-h-screen flex items-center justify-center">
<div class="bg-gray-800 rounded-xl p-8 max-w-lg w-full mx-4 shadow-2xl">
  <h1 class="text-2xl font-bold mb-4">📁 {filename}</h1>
  <p class="text-gray-400 mb-6">Size: {size_mb:.1f} MB &middot; Expires: {meta["expires_at"][:16].replace("T", " ")} UTC</p>
  <a href="/d/{file_id}?dl=1" class="block w-full bg-blue-600 hover:bg-blue-700 text-center py-3 rounded-lg font-semibold mb-4">Download</a>
  <div class="bg-gray-900 rounded p-3 font-mono text-sm text-gray-300 mb-2">curl -OJ {download_url}</div>
  <div class="bg-gray-900 rounded p-3 font-mono text-sm text-gray-300">wget --content-disposition {download_url}</div>
</div></body></html>""")

    encoded_filename = quote(meta["original_filename"])
    return FileResponse(
        path=bin_path,
        filename=meta["original_filename"],
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{encoded_filename}"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/api/info/{file_id}")
async def file_info(file_id: str):
    if not VALID_ID.match(file_id):
        raise HTTPException(status_code=400, detail="Invalid file ID")

    meta = get_file_meta(file_id)
    if meta is None:
        raise HTTPException(status_code=410, detail="File expired or not found")

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
