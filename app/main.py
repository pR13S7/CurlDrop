from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.routes import upload, download
from app.config import UPLOAD_DIR

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="File Share", docs_url=None, redoc_url=None)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(upload.router)
app.include_router(download.router)

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
