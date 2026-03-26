from typing import Any, Dict, List, Optional, Tuple

from app.schemas.response import AttractionInfo, Location
from app.tools.provider import get_tool_provider
from app.utils.config import IMAGE_LOOKUP_LIMIT


MAX_ATTRACTIONS = 5

PREFERENCE_ALIASES = {
    "history": "历史",
    "historical": "历史",
    "museum": "历史",
    "food": "美食",
    "foods": "美食",
    "eat": "美食",
    "photo": "拍照",
    "photos": "拍照",
    "photography": "拍照",
    "picture": "拍照",
}

CATEGORY_RULES = [
    ("博物馆", ["博物馆", "展览馆", "纪念馆"]),
    ("历史文化", ["文物", "古城", "古镇", "古村", "遗址", "故居", "历史", "名胜"]),
    ("自然景观", ["风景名胜", "自然保护区", "山", "湖", "湿地", "峡谷", "瀑布"]),
    ("休闲公园", ["公园", "植物园", "动物园"]),
    ("城市地标", ["地标", "观景", "广场", "塔", "电视塔", "摩天轮"]),
    ("艺术展馆", ["美术馆", "艺术馆", "文化宫"]),
    ("宗教古建", ["寺庙", "教堂", "清真寺", "道观", "古建筑"]),
    ("美食街区", ["美食", "餐饮", "小吃", "食府", "餐厅", "美食街"]),
    ("夜游市集", ["夜市", "步行街"]),
]

DESCRIPTION_TEMPLATES = {
    "博物馆": "{name}适合系统了解当地的人文与馆藏，适合作为行程中的核心参观点。",
    "历史文化": "{name}更适合体验目的地的历史脉络与城市记忆，游览节奏会比较从容。",
    "自然景观": "{name}适合放慢节奏看风景，也比较适合拍照和轻松散步。",
    "休闲公园": "{name}适合休闲漫步与放松，适合作为行程中的轻量安排。",
    "城市地标": "{name}是很适合打卡拍照的代表性地点，辨识度比较高。",
    "艺术展馆": "{name}适合偏好艺术与展览内容的行程安排，观展体验会更集中。",
    "宗教古建": "{name}适合感受传统建筑与文化氛围，整体游览体验更安静。",
    "美食街区": "{name}适合集中体验本地风味，可以把餐饮安排和游览结合起来。",
    "夜游市集": "{name}更适合安排在傍晚或夜间，边逛边吃的体验会更自然。",
}

DURATION_RULES = {
    "博物馆": (180, "3小时"),
    "历史文化": (180, "3小时"),
    "自然景观": (150, "2.5小时"),
    "休闲公园": (120, "2小时"),
    "城市地标": (90, "1.5小时"),
    "艺术展馆": (150, "2.5小时"),
    "宗教古建": (120, "2小时"),
    "美食街区": (120, "2小时"),
    "夜游市集": (120, "2小时"),
}

TICKET_RULES = {
    "博物馆": (60.0, "门票为经验估算，实际价格请以景区公布为准。"),
    "历史文化": (60.0, "门票为经验估算，实际价格请以景区公布为准。"),
    "自然景观": (40.0, "门票为经验估算，实际价格请以景区公布为准。"),
    "休闲公园": (20.0, "门票为经验估算，实际价格请以景区公布为准。"),
    "城市地标": (40.0, "门票为经验估算，实际价格请以景区公布为准。"),
    "艺术展馆": (50.0, "门票为经验估算，实际价格请以景区公布为准。"),
    "宗教古建": (30.0, "门票为经验估算，实际价格请以景区公布为准。"),
    "美食街区": (0.0, "通常无单独门票，以现场消费为主。"),
    "夜游市集": (0.0, "通常无单独门票，以现场消费为主。"),
}


def _normalize_preferences(preferences: List[str]) -> List[str]:
    normalized: List[str] = []
    for item in preferences:
        text = item.strip()
        if not text:
            continue

        mapped = PREFERENCE_ALIASES.get(text.lower(), text)
        if mapped not in normalized:
            normalized.append(mapped)
    return normalized


def _keywords_from_preferences(preferences: List[str]) -> List[str]:
    normalized = _normalize_preferences(preferences)
    keywords: List[str] = []

    if "历史" in normalized:
        keywords.extend(["博物馆", "古城", "历史遗址"])
    if "美食" in normalized:
        keywords.extend(["美食街", "夜市", "小吃街"])
    if "拍照" in normalized:
        keywords.extend(["地标", "公园", "观景台"])

    if not keywords:
        keywords.append("热门景点")

    return keywords


def _build_mock_attraction(
    *,
    name: str,
    description: str,
    suggested_duration: str,
    visit_duration: int,
    destination: str,
    category: str,
    longitude: float,
    latitude: float,
) -> AttractionInfo:
    price, note = TICKET_RULES.get(category, (None, None))
    return AttractionInfo(
        name=name,
        address=f"{destination}热门区域",
        location=Location(longitude=longitude, latitude=latitude),
        description=description,
        visit_duration=visit_duration,
        suggested_duration=suggested_duration,
        category=category,
        rating=None,
        image_url=None,
        ticket_price=price,
        ticket_price_note=note,
    )


def _fallback_attractions(destination: str, preferences: List[str]) -> List[AttractionInfo]:
    normalized = _normalize_preferences(preferences)

    if "历史" in normalized:
        return [
            _build_mock_attraction(
                name=f"{destination}历史博物馆",
                description="适合系统了解当地历史文化，适合作为首站参观。",
                suggested_duration="2小时",
                visit_duration=120,
                destination=destination,
                category="历史文化",
                longitude=116.397128,
                latitude=39.916527,
            ),
            _build_mock_attraction(
                name=f"{destination}古城街区",
                description="适合步行游览，感受城市旧城区的氛围与街巷节奏。",
                suggested_duration="2.5小时",
                visit_duration=150,
                destination=destination,
                category="历史文化",
                longitude=116.403963,
                latitude=39.915119,
            ),
        ]

    if "美食" in normalized:
        return [
            _build_mock_attraction(
                name=f"{destination}美食街",
                description="适合集中体验当地风味，把逛吃安排在同一段行程里。",
                suggested_duration="2小时",
                visit_duration=120,
                destination=destination,
                category="美食街区",
                longitude=116.41,
                latitude=39.92,
            ),
            _build_mock_attraction(
                name=f"{destination}夜市",
                description="适合傍晚后出行，边逛边吃会更有氛围。",
                suggested_duration="2小时",
                visit_duration=120,
                destination=destination,
                category="夜游市集",
                longitude=116.42,
                latitude=39.93,
            ),
        ]

    if "拍照" in normalized:
        return [
            _build_mock_attraction(
                name=f"{destination}城市地标",
                description="适合打卡拍照，代表性强，行程识别度也高。",
                suggested_duration="1.5小时",
                visit_duration=90,
                destination=destination,
                category="城市地标",
                longitude=116.397128,
                latitude=39.916527,
            ),
            _build_mock_attraction(
                name=f"{destination}观景公园",
                description="适合轻松散步和拍照，节奏更舒缓。",
                suggested_duration="2小时",
                visit_duration=120,
                destination=destination,
                category="休闲公园",
                longitude=116.385,
                latitude=39.905,
            ),
        ]

    return [
        _build_mock_attraction(
            name=f"{destination}热门景点",
            description="适合作为初次到访时的代表性打卡点，安排起来也更稳妥。",
            suggested_duration="2小时",
            visit_duration=120,
            destination=destination,
            category="城市地标",
            longitude=116.397128,
            latitude=39.916527,
        ),
        _build_mock_attraction(
            name=f"{destination}城市公园",
            description="适合放慢节奏散步休息，让行程更均衡。",
            suggested_duration="1.5小时",
            visit_duration=90,
            destination=destination,
            category="休闲公园",
            longitude=116.385,
            latitude=39.905,
        ),
    ]


def _parse_rating(poi: Dict[str, Any]) -> Optional[float]:
    rating = poi.get("rating")
    if rating in (None, "", []):
        return None

    try:
        return float(rating)
    except (TypeError, ValueError):
        return None


def _clean_type_tokens(poi: Dict[str, Any]) -> List[str]:
    raw_tokens = poi.get("type_tokens") or []
    if not isinstance(raw_tokens, list):
        return []

    cleaned: List[str] = []
    seen = set()
    for item in raw_tokens:
        token = str(item).strip()
        if not token or token in seen:
            continue
        seen.add(token)
        cleaned.append(token)
    return cleaned


def _normalize_category(type_tokens: List[str]) -> Optional[str]:
    if not type_tokens:
        return None

    for category, keywords in CATEGORY_RULES:
        if any(any(keyword in token for keyword in keywords) for token in type_tokens):
            return category

    return type_tokens[-1]


def _build_description(name: str, category: Optional[str], destination: str) -> str:
    if category and category in DESCRIPTION_TEMPLATES:
        return DESCRIPTION_TEMPLATES[category].format(name=name, destination=destination)
    return f"{name}适合作为在{destination}旅行时的顺路停留点，整体节奏会比较轻松。"


def _duration_by_category(category: Optional[str]) -> Tuple[int, str]:
    if category and category in DURATION_RULES:
        return DURATION_RULES[category]
    return (120, "2小时")


def _ticket_info_by_category(category: Optional[str]) -> Tuple[Optional[float], Optional[str]]:
    if category and category in TICKET_RULES:
        return TICKET_RULES[category]
    return (None, None)


def _poi_to_attraction(poi: Dict[str, Any], destination: str) -> Optional[AttractionInfo]:
    parsed_location = poi.get("parsed_location")
    if not isinstance(parsed_location, dict):
        return None

    longitude = parsed_location.get("longitude")
    latitude = parsed_location.get("latitude")
    if not isinstance(longitude, float) or not isinstance(latitude, float):
        return None

    name = str(poi.get("name", "")).strip()
    address = str(poi.get("address", "")).strip()
    if not name or not address:
        return None

    type_tokens = _clean_type_tokens(poi)
    category = _normalize_category(type_tokens)
    visit_duration, suggested_duration = _duration_by_category(category)
    ticket_price, ticket_price_note = _ticket_info_by_category(category)

    return AttractionInfo(
        name=name,
        address=address,
        location=Location(longitude=longitude, latitude=latitude),
        description=_build_description(name, category, destination),
        visit_duration=visit_duration,
        suggested_duration=suggested_duration,
        category=category,
        rating=_parse_rating(poi),
        image_url=None,
        ticket_price=ticket_price,
        ticket_price_note=ticket_price_note,
    )


def _image_query_for_attraction(attraction: AttractionInfo, destination: str) -> str:
    parts = [destination, attraction.name]
    if attraction.category:
        parts.append(attraction.category)
    return " ".join(parts)


def _attach_images(attractions: List[AttractionInfo], destination: str) -> List[AttractionInfo]:
    if not attractions or IMAGE_LOOKUP_LIMIT <= 0:
        return attractions

    tools = get_tool_provider()
    enriched: List[AttractionInfo] = []
    for index, attraction in enumerate(attractions):
        if index >= IMAGE_LOOKUP_LIMIT or attraction.image_url:
            enriched.append(attraction)
            continue

        image_url = None
        try:
            image_url = tools.search_image(_image_query_for_attraction(attraction, destination))
        except Exception as exc:
            print(f"[image_service] 景点图片搜索失败，继续使用占位样式：{exc}")

        enriched.append(attraction.model_copy(update={"image_url": image_url}))

    return enriched


def get_attractions(destination: str, preferences: List[str]) -> List[AttractionInfo]:
    """
    景点搜索 Agent:
    1. 将用户偏好映射为高德搜索关键词
    2. 对每个关键词调用高德文本搜索
    3. 合并结果并按 name + address 去重
    4. 映射为 AttractionInfo
    5. 为前几个重点景点补充图片
    6. 失败时回退到本地 mock 数据
    """

    keywords = _keywords_from_preferences(preferences)
    tools = get_tool_provider()
    unique_attractions: Dict[Tuple[str, str], AttractionInfo] = {}

    try:
        for keyword in keywords:
            pois = tools.search_pois(keywords=keyword, city=destination, page_size=6)
            for poi in pois:
                attraction = _poi_to_attraction(poi, destination)
                if not attraction:
                    continue

                dedupe_key = (attraction.name, attraction.address)
                if dedupe_key not in unique_attractions:
                    unique_attractions[dedupe_key] = attraction

            if len(unique_attractions) >= MAX_ATTRACTIONS:
                break
    except Exception as exc:
        print(f"[attraction_agent] 高德 POI 搜索失败，回退到 mock：{exc}")
        return _fallback_attractions(destination, preferences)

    if unique_attractions:
        attractions = list(unique_attractions.values())[:MAX_ATTRACTIONS]
        return _attach_images(attractions, destination)

    return _fallback_attractions(destination, preferences)
