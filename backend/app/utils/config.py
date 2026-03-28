import os

from dotenv import load_dotenv

load_dotenv()


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default

    try:
        return int(value)
    except ValueError:
        return default


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_list(name: str, default: list[str] | None = None) -> list[str]:
    value = os.getenv(name, "")
    if not value:
        return list(default or [])
    return [item.strip() for item in value.split(",") if item.strip()]


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "")
AMAP_API_KEY = os.getenv("AMAP_API_KEY", "")

APP_ENV = os.getenv("APP_ENV", "development")
APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = _get_int("PORT", _get_int("APP_PORT", 8000))
OPEN_BROWSER_ON_START = _get_bool("OPEN_BROWSER_ON_START", True)

DEFAULT_CORS_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]
CORS_ALLOW_ORIGINS = _get_list("CORS_ALLOW_ORIGINS", DEFAULT_CORS_ORIGINS)

WEATHER_API_TIMEOUT_SECONDS = _get_int("WEATHER_API_TIMEOUT_SECONDS", 10)
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")
IMAGE_API_TIMEOUT_SECONDS = _get_int("IMAGE_API_TIMEOUT_SECONDS", 8)
IMAGE_LOOKUP_LIMIT = _get_int("IMAGE_LOOKUP_LIMIT", 3)
