import json
from typing import Dict, List, Tuple
from urllib.parse import urlencode
from urllib.request import urlopen

from app.utils.config import WEATHER_API_TIMEOUT_SECONDS


OPEN_METEO_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODE_LABELS = {
    0: "晴",
    1: "大致晴朗",
    2: "局部多云",
    3: "阴",
    45: "雾",
    48: "冻雾",
    51: "毛毛雨",
    53: "小雨",
    55: "中雨",
    56: "冻毛毛雨",
    57: "冻毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    66: "冻雨",
    67: "冻雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    77: "阵雪",
    80: "阵雨",
    81: "强阵雨",
    82: "暴雨",
    85: "阵雪",
    86: "强阵雪",
    95: "雷暴",
    96: "雷暴伴冰雹",
    99: "强雷暴伴冰雹",
}


def _get_json(url: str) -> Dict:
    with urlopen(url, timeout=WEATHER_API_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def _format_temperature(min_temp: float, max_temp: float) -> str:
    return f"{round(min_temp)}°C - {round(max_temp)}°C"


def _weather_label(code: int) -> str:
    return WEATHER_CODE_LABELS.get(code, "天气待确认")


def _resolve_city_coordinates(city: str) -> Tuple[float, float]:
    params = {
        "name": city,
        "count": 1,
        "language": "zh",
        "format": "json",
    }
    url = f"{OPEN_METEO_GEOCODING_URL}?{urlencode(params)}"
    payload = _get_json(url)

    results = payload.get("results")
    if not isinstance(results, list) or not results:
        raise ValueError(f"未找到城市对应坐标：{city}")

    first = results[0]
    latitude = first.get("latitude")
    longitude = first.get("longitude")
    if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
        raise ValueError(f"城市坐标解析失败：{city}")

    return float(latitude), float(longitude)


def fetch_daily_weather(city: str, dates: List[str]) -> List[Dict[str, str]]:
    if not dates:
        return []

    latitude, longitude = _resolve_city_coordinates(city)
    start_date = min(dates)
    end_date = max(dates)

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "weather_code,temperature_2m_max,temperature_2m_min",
        "timezone": "auto",
        "start_date": start_date,
        "end_date": end_date,
    }
    url = f"{OPEN_METEO_FORECAST_URL}?{urlencode(params)}"
    payload = _get_json(url)

    daily = payload.get("daily")
    if not isinstance(daily, dict):
        raise ValueError("天气接口返回缺少 daily 字段")

    times = daily.get("time")
    codes = daily.get("weather_code")
    max_temps = daily.get("temperature_2m_max")
    min_temps = daily.get("temperature_2m_min")

    if not all(isinstance(item, list) for item in [times, codes, max_temps, min_temps]):
        raise ValueError("天气接口返回格式异常")

    weather_by_date: Dict[str, Dict[str, str]] = {}
    for date, code, max_temp, min_temp in zip(times, codes, max_temps, min_temps):
        if not isinstance(date, str):
            continue
        if not isinstance(code, (int, float)):
            continue
        if not isinstance(max_temp, (int, float)) or not isinstance(min_temp, (int, float)):
            continue

        weather_by_date[date] = {
            "date": date,
            "weather": _weather_label(int(code)),
            "temperature": _format_temperature(float(min_temp), float(max_temp)),
        }

    results: List[Dict[str, str]] = []
    for date in dates:
        item = weather_by_date.get(date)
        if not item:
            raise ValueError(f"天气接口缺少日期数据：{date}")
        results.append(item)

    return results
