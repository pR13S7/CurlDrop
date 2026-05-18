import os
from pathlib import Path

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/data/uploads"))
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 209715200))  # 200MB
FILE_TTL_HOURS = int(os.getenv("FILE_TTL_HOURS", 24))
ID_LENGTH = 8
