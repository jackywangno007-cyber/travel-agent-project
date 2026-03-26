import json
from typing import Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.utils.config import IMAGE_API_TIMEOUT_SECONDS, UNSPLASH_ACCESS_KEY


UNSPLASH_SEARCH_URL = "https://api.unsplash.com/search/photos"


def search_unsplash_image(query: str) -> Optional[str]:
    if not UNSPLASH_ACCESS_KEY or not query.strip():
        return None

    params = urlencode(
        {
            "query": query.strip(),
            "page": 1,
            "per_page": 1,
            "orientation": "landscape",
            "content_filter": "high",
        }
    )
    request = Request(
        f"{UNSPLASH_SEARCH_URL}?{params}",
        headers={
            "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}",
            "Accept-Version": "v1",
        },
    )

    with urlopen(request, timeout=IMAGE_API_TIMEOUT_SECONDS) as response:
        payload = json.loads(response.read().decode("utf-8"))

    results = payload.get("results")
    if not isinstance(results, list) or not results:
        return None

    first = results[0]
    if not isinstance(first, dict):
        return None

    urls = first.get("urls")
    if not isinstance(urls, dict):
        return None

    for key in ["small", "regular", "thumb"]:
        value = urls.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return None
