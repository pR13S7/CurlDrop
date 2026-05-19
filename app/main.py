from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.routes import upload, download
from app.config import UPLOAD_DIR, FILE_TTL_HOURS, MAX_FILE_SIZE

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="File Share", docs_url=None, redoc_url=None)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(upload.router)
app.include_router(download.router)


@app.get("/api/config")
async def get_config():
    return {"ttl_hours": FILE_TTL_HOURS, "max_file_size": MAX_FILE_SIZE}

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
