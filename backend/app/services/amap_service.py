import json
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode
from urllib.request import urlopen

from app.utils.config import AMAP_API_KEY


AMAP_TEXT_SEARCH_URL = "https://restapi.amap.com/v3/place/text"


def _parse_location(location: str) -> Optional[Dict[str, float]]:
    if not location:
        return None

    parts = location.split(",")
    if len(parts) != 2:
        return None

    try:
        longitude = float(parts[0].strip())
        latitude = float(parts[1].strip())
    except ValueError:
        return None

    return {"longitude": longitude, "latitude": latitude}


def _split_type_tokens(raw_type: str) -> List[str]:
    if not raw_type:
        return []

    tokens: List[str] = []
    seen = set()

    for part in raw_type.split(";"):
        token = part.strip()
        if not token or token in seen:
            continue
        seen.add(token)
        tokens.append(token)

    return tokens


def _clean_poi(poi: Dict[str, Any]) -> Dict[str, Any]:
    raw_type = str(poi.get("type", "")).strip()
    parsed_location = _parse_location(str(poi.get("location", "")).strip())

    return {
        **poi,
        "name": str(poi.get("name", "")).strip(),
        "address": str(poi.get("address", "")).strip(),
        "raw_type": raw_type,
        "type_tokens": _split_type_tokens(raw_type),
        "parsed_location": parsed_location,
    }


def search_pois(
    *,
    keywords: str,
    city: str,
    page_size: int = 10,
    page: int = 1,
) -> List[Dict[str, Any]]:
    if not AMAP_API_KEY:
        raise ValueError("AMAP_API_KEY 未配置")

    params = {
        "key": AMAP_API_KEY,
        "keywords": keywords,
        "city": city,
        "offset": page_size,
        "page": page,
        "extensions": "all",
    }
    url = f"{AMAP_TEXT_SEARCH_URL}?{urlencode(params)}"

    with urlopen(url, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))

    if payload.get("status") != "1":
        info = payload.get("info", "高德接口请求失败")
        raise ValueError(f"高德 POI 搜索失败：{info}")

    pois = payload.get("pois", [])
    if not isinstance(pois, list):
        raise ValueError("高德 POI 搜索返回格式异常")

    return [_clean_poi(poi) for poi in pois if isinstance(poi, dict)]
