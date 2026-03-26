from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from app.schemas.response import HotelInfo, Location
from app.services.amap_service import search_pois
from app.services.image_service import search_unsplash_image
from app.services.weather_service import fetch_daily_weather


def _hotel_price_estimate(destination: str, budget: Optional[float], rank: int) -> tuple[float, str]:
    if budget is None:
        base = 420.0
    else:
        # Keep some room for tickets, food and transport; hotel uses about 20%-35% of budget.
        daily_allowance = max(budget / 4, 180.0)
        base = min(max(daily_allowance * 0.35, 180.0), 980.0)

    adjusted = base + rank * 60.0
    city_factor = 1.0
    if destination in {"北京", "上海", "深圳", "广州", "杭州"}:
        city_factor = 1.18
    elif destination in {"成都", "重庆", "西安", "南京", "苏州"}:
        city_factor = 1.08

    estimated = round(adjusted * city_factor / 10) * 10
    note = "酒店价格为基于城市级别、预算范围和酒店排序的经验估算。"
    return float(estimated), note


def _build_hotel_description(name: str, category: Optional[str], address: str) -> str:
    if category:
        return f"{name} 属于 {category} 类型，位置在 {address} 附近，适合作为行程中的住宿落点。"
    return f"{name} 位于 {address} 附近，便于衔接景点游览与城市内出行。"


def _build_fallback_hotel(destination: str, budget: Optional[float]) -> HotelInfo:
    if budget is not None and budget < 1000:
        nightly_price = 199.0
        name = f"{destination}经济型酒店"
        location_summary = "地铁站附近，交通便利"
    elif budget is not None and budget < 3000:
        nightly_price = 399.0
        name = f"{destination}舒适型酒店"
        location_summary = "市中心商圈附近"
    else:
        nightly_price = 699.0
        name = f"{destination}精选高档酒店"
        location_summary = "核心景区附近，配套完善"

    return HotelInfo(
        name=name,
        address=f"{destination}核心城区",
        location=Location(longitude=116.397428, latitude=39.90923),
        price_per_night=nightly_price,
        location_summary=location_summary,
        description=f"{name} 为当前的兜底住宿推荐，适合作为 {destination} 行程中的稳定落脚点。",
        price_note="该价格为模板酒店的经验估算。",
    )


@dataclass
class ToolProvider:
    """
    Shared tool provider for agent-facing capabilities.

    The provider keeps the current project runnable with HTTP services and local rules,
    while exposing a stable interface that can later be swapped to MCP-backed tools.
    """

    def search_pois(self, *, keywords: str, city: str, page_size: int = 10, page: int = 1):
        return search_pois(keywords=keywords, city=city, page_size=page_size, page=page)

    def fetch_daily_weather(self, city: str, dates: List[str]) -> List[Dict[str, str]]:
        return fetch_daily_weather(city, dates)

    def search_image(self, query: str) -> Optional[str]:
        return search_unsplash_image(query)

    def recommend_hotel(self, destination: str, budget: Optional[float]) -> HotelInfo:
        hotel_keywords = ["高评分酒店", "精选酒店", "酒店"]

        for keyword in hotel_keywords:
            try:
                pois = self.search_pois(keywords=keyword, city=destination, page_size=8)
            except Exception:
                continue

            ranked_candidates = []
            for poi in pois:
                parsed_location = poi.get("parsed_location")
                if not isinstance(parsed_location, dict):
                    continue

                longitude = parsed_location.get("longitude")
                latitude = parsed_location.get("latitude")
                if not isinstance(longitude, (int, float)) or not isinstance(latitude, (int, float)):
                    continue

                name = str(poi.get("name", "")).strip()
                address = str(poi.get("address", "")).strip() or f"{destination}城区"
                if not name:
                    continue

                type_tokens = poi.get("type_tokens")
                category = None
                if isinstance(type_tokens, list):
                    cleaned = [token for token in type_tokens if isinstance(token, str) and token.strip()]
                    category = cleaned[-1] if cleaned else None

                ranked_candidates.append(
                    {
                        "name": name,
                        "address": address,
                        "location": Location(longitude=float(longitude), latitude=float(latitude)),
                        "category": category,
                    }
                )

            if not ranked_candidates:
                continue

            selected = ranked_candidates[0]
            price, price_note = _hotel_price_estimate(destination, budget, rank=0)

            return HotelInfo(
                name=selected["name"],
                address=selected["address"],
                location=selected["location"],
                price_per_night=price,
                location_summary=selected["address"],
                description=_build_hotel_description(
                    selected["name"],
                    selected["category"],
                    selected["address"],
                ),
                price_note=price_note,
            )

        return _build_fallback_hotel(destination, budget)


_shared_provider: Optional[ToolProvider] = None


def get_tool_provider() -> ToolProvider:
    global _shared_provider
    if _shared_provider is None:
        _shared_provider = ToolProvider()
    return _shared_provider


def set_tool_provider(provider: ToolProvider) -> None:
    global _shared_provider
    _shared_provider = provider
