from pathlib import Path
from typing import Optional

from starlette.config import Config
from starlette.datastructures import Secret

p: Path = Path(__file__).parents[1] / ".env"
config: Config = Config(p if p.exists() else None)

DATABASE: str = config("DATABASE", cast=str)
DB_USER: Optional[str] = config("DB_USER", cast=str, default=None)
DB_PASSWORD: Optional[Secret] = config("DB_PASSWORD", cast=Secret, default=None)
DB_HOST: str = config("DB_HOST", cast=str, default="localhost")
DB_PORT: int = config("DB_PORT", cast=int, default=5432)

TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "host": DB_HOST,
                "port": DB_PORT,
                "user": DB_USER,
                "password": str(DB_PASSWORD),
                "database": DATABASE,
            },
        },
    },
    "apps": {
        "fairy_note": {
            "models": ["fairy_note.models", "aerich.models"],
            "default_connection": "default",
        },
    },
    "timezone": "Asia/Shanghai",
}

# recommend:
# get a string by run
# openssl rand -hex 32
JWT_SECRET_KEY: str = config("JWT_SECRET_KEY", cast=str)
JWT_EXPIRE_HOURS: int = config("JWT_EXPIRE_HOURS", cast=int, default=720)
JWT_ALGORITHM: str = config("JWT_ALGORITHM")

BARRAGE_MESSAGE_TYPE = config("BARRAGE_MESSAGE_TYPE", cast=str, default="chatmsg")
BARRAGE_TABLE_NAME = config("BARRAGE_TABLE_NAME", cast=str)

ROOM_ID = config("ROOM_ID", cast=str)

API_PREFIX = config("API_PREFIX", cast=str, default="/api/v1")
