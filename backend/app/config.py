import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

# database url
db_name = os.getenv("DATABASE_URL", "db.sqlite3")
DATABASE_URL = f'sqlite+aiosqlite:///{BASE_DIR / db_name}'

# to get a string like this run: `openssl rand -hex 32``
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dsdsdsdsdsdsdsdsdsdsdsdsdsdsdsdsdsdsdsd")

JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))