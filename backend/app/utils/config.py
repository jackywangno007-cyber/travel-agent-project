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

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "")
AMAP_API_KEY = os.getenv("AMAP_API_KEY", "")
WEATHER_API_TIMEOUT_SECONDS = _get_int("WEATHER_API_TIMEOUT_SECONDS", 10)
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")
IMAGE_API_TIMEOUT_SECONDS = _get_int("IMAGE_API_TIMEOUT_SECONDS", 8)
IMAGE_LOOKUP_LIMIT = _get_int("IMAGE_LOOKUP_LIMIT", 3)
