from typing import List

from app.schemas.response import WeatherInfo
from app.tools.provider import get_tool_provider


def _mock_weather(dates: List[str]) -> List[WeatherInfo]:
    mock_weather_cycle = [
        ("晴", "18°C - 26°C"),
        ("多云", "17°C - 24°C"),
        ("小雨", "16°C - 22°C"),
    ]

    results: List[WeatherInfo] = []
    for idx, date in enumerate(dates):
        weather, temperature = mock_weather_cycle[idx % len(mock_weather_cycle)]
        results.append(
            WeatherInfo(
                date=date,
                weather=weather,
                temperature=temperature,
            )
        )
    return results


def get_weather(destination: str, dates: List[str]) -> List[WeatherInfo]:
    """
    天气查询 Agent：
    1. 优先调用真实天气服务按日期返回结果
    2. 如果天气服务失败，则自动回退到 mock 数据
    3. 返回结果与传入 dates 严格对齐
    """

    if not dates:
        return []

    try:
        weather_items = get_tool_provider().fetch_daily_weather(destination, dates)
        return [
            WeatherInfo(
                date=item["date"],
                weather=item["weather"],
                temperature=item["temperature"],
            )
            for item in weather_items
        ]
    except Exception as exc:
        print(f"[weather_agent] 真实天气查询失败，回退到 mock：{exc}")
        return _mock_weather(dates)
