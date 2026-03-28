from typing import Dict, List, Optional

from app.schemas.response import DayMeals, MealInfo
from app.tools.provider import get_tool_provider


MEAL_SLOTS = ["breakfast", "lunch", "dinner", "snack"]

MEAL_SLOT_CONFIG = {
    "breakfast": {
        "keywords": ["早餐店", "包子铺", "面馆"],
        "label": "早餐",
        "default_cost": 18.0,
        "category": "早餐",
    },
    "lunch": {
        "keywords": ["餐厅", "家常菜", "本地菜"],
        "label": "午餐",
        "default_cost": 42.0,
        "category": "午餐",
    },
    "dinner": {
        "keywords": ["特色餐厅", "晚餐", "美食"],
        "label": "晚餐",
        "default_cost": 58.0,
        "category": "晚餐",
    },
    "snack": {
        "keywords": ["小吃", "甜品", "饮品"],
        "label": "小吃",
        "default_cost": 22.0,
        "category": "小吃",
    },
}


def _normalize_preferences(preferences: Optional[List[str]]) -> List[str]:
    if not preferences:
        return []

    normalized: List[str] = []
    for item in preferences:
        text = item.strip()
        if text and text not in normalized:
            normalized.append(text)
    return normalized


def _keywords_for_slot(slot: str, preferences: Optional[List[str]]) -> List[str]:
    keywords = list(MEAL_SLOT_CONFIG[slot]["keywords"])
    normalized = _normalize_preferences(preferences)

    if "美食" in normalized:
        if slot in {"lunch", "dinner"}:
            keywords = ["老字号", "本地菜", "特色餐厅"] + keywords
        if slot == "snack":
            keywords = ["小吃街", "夜市"] + keywords
    if "夜景" in normalized and slot in {"dinner", "snack"}:
        keywords = ["夜景餐厅", "江景餐厅"] + keywords
    if "海边" in normalized and slot in {"lunch", "dinner"}:
        keywords = ["海鲜", "海景餐厅"] + keywords
    if "情侣" in normalized and slot == "dinner":
        keywords = ["约会餐厅", "景观餐厅"] + keywords

    unique_keywords: List[str] = []
    for keyword in keywords:
        if keyword not in unique_keywords:
            unique_keywords.append(keyword)
    return unique_keywords


def _parse_rating(poi: Dict) -> Optional[float]:
    rating = poi.get("rating")
    if rating in (None, "", []):
        return None

    try:
        return float(rating)
    except (TypeError, ValueError):
        return None


def _fallback_meal(slot: str, destination: str) -> MealInfo:
    config = MEAL_SLOT_CONFIG[slot]
    return MealInfo(
        meal_type=slot,  # type: ignore[arg-type]
        name=f"{destination}{config['label']}推荐",
        address=f"{destination}热门商圈附近",
        description=f"作为{config['label']}的兜底推荐，适合在核心行程附近快速就餐。",
        estimated_cost=config["default_cost"],
        category=config["category"],
        rating=None,
        source="fallback",
    )


def _poi_to_meal(slot: str, poi: Dict, destination: str) -> Optional[MealInfo]:
    name = str(poi.get("name", "")).strip()
    address = str(poi.get("address", "")).strip()
    if not name:
        return None

    config = MEAL_SLOT_CONFIG[slot]
    category_tokens = poi.get("type_tokens") or []
    category = config["category"]
    if isinstance(category_tokens, list) and category_tokens:
        category = str(category_tokens[-1]).strip() or config["category"]

    return MealInfo(
        meal_type=slot,  # type: ignore[arg-type]
        name=name,
        address=address or f"{destination}热门商圈附近",
        description=f"{name}适合作为在{destination}行程中的{config['label']}安排，便于顺路就餐。",
        estimated_cost=config["default_cost"],
        category=category,
        rating=_parse_rating(poi),
        source="poi",
    )


def build_fallback_day_meals(destination: str, day_index: int = 1) -> DayMeals:
    return DayMeals(
        breakfast=_fallback_meal("breakfast", destination),
        lunch=_fallback_meal("lunch", destination),
        dinner=_fallback_meal("dinner", destination),
        snack=_fallback_meal("snack", destination),
    )


def meal_cost(day_meals: Optional[DayMeals]) -> float:
    if not day_meals:
        return 0.0

    return sum(
        meal.estimated_cost if meal else 0.0
        for meal in [
            day_meals.breakfast,
            day_meals.lunch,
            day_meals.dinner,
            day_meals.snack,
        ]
    )


def ensure_day_meals(
    meals: Optional[DayMeals],
    destination: str,
    day_index: int,
    meal_candidates: Optional[Dict[str, List[MealInfo]]] = None,
) -> DayMeals:
    candidate_map = meal_candidates or {}

    def pick(slot: str) -> MealInfo:
        existing = getattr(meals, slot, None) if meals else None
        if existing:
            return existing

        options = candidate_map.get(slot, [])
        if options:
            return options[(day_index - 1) % len(options)]

        return _fallback_meal(slot, destination)

    return DayMeals(
        breakfast=pick("breakfast"),
        lunch=pick("lunch"),
        dinner=pick("dinner"),
        snack=pick("snack"),
    )


def get_meal_candidates(destination: str, preferences: Optional[List[str]] = None) -> Dict[str, List[MealInfo]]:
    results: Dict[str, List[MealInfo]] = {slot: [] for slot in MEAL_SLOTS}
    tools = get_tool_provider()

    try:
        for slot in MEAL_SLOTS:
            unique_meals: List[MealInfo] = []
            seen = set()

            for keyword in _keywords_for_slot(slot, preferences):
                pois = tools.search_pois(keywords=keyword, city=destination, page_size=6)
                for poi in pois:
                    meal = _poi_to_meal(slot, poi, destination)
                    if not meal:
                        continue

                    dedupe_key = (meal.name, meal.address)
                    if dedupe_key in seen:
                        continue

                    seen.add(dedupe_key)
                    unique_meals.append(meal)

                if len(unique_meals) >= 5:
                    break

            results[slot] = unique_meals if unique_meals else [_fallback_meal(slot, destination)]

    except Exception as exc:
        print(f"[meal_agent] 餐饮 POI 搜索失败，回退到默认餐饮：{exc}")
        return {
            "breakfast": [_fallback_meal("breakfast", destination)],
            "lunch": [_fallback_meal("lunch", destination)],
            "dinner": [_fallback_meal("dinner", destination)],
            "snack": [_fallback_meal("snack", destination)],
        }

    return results
