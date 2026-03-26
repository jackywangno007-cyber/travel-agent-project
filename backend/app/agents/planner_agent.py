import json
import math
import re
from typing import Any, Dict, List, Optional, Set

from app.schemas.request import TripPlanRequest
from app.schemas.response import (
    AttractionInfo,
    DayMeals,
    DayPlan,
    HotelInfo,
    MealInfo,
    TransportationInfo,
    TripPlanResponse,
    WeatherInfo,
)
from app.services.llm_service import chat_json


MEAL_SLOTS = ["breakfast", "lunch", "dinner", "snack"]


def _compute_meal_cost(meals: DayMeals) -> float:
    return sum(
        meal.estimated_cost if meal else 0.0
        for meal in [meals.breakfast, meals.lunch, meals.dinner, meals.snack]
    )


def _compute_estimated_cost(
    day_attractions: List[AttractionInfo], day_meals: DayMeals, hotel: HotelInfo
) -> float:
    attraction_cost = sum(item.ticket_price or 0 for item in day_attractions)
    return hotel.price_per_night + attraction_cost + _compute_meal_cost(day_meals) + 80.0


def _safe_float(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and value.strip():
        return float(value.strip())
    raise ValueError("estimated_cost 必须是数字")


def _validate_summary(llm_result: Dict[str, Any]) -> str:
    summary = llm_result.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError("LLM 返回的 summary 为空")
    return summary.strip()


def _validate_daily_plan_shape(
    llm_result: Dict[str, Any], expected_dates: List[str]
) -> List[Dict[str, Any]]:
    raw_days = llm_result.get("daily_plan")
    if not isinstance(raw_days, list) or not raw_days:
        raise ValueError("LLM 返回的 daily_plan 缺失或为空")
    if len(raw_days) != len(expected_dates):
        raise ValueError(
            f"LLM 返回的天数不一致：期望 {len(expected_dates)} 天，实际 {len(raw_days)} 天"
        )

    for idx, day in enumerate(raw_days, start=1):
        if not isinstance(day, dict):
            raise ValueError(f"第 {idx} 天的数据格式不正确")

    return raw_days


def _dedupe_preserve_order(names: List[str]) -> List[str]:
    result: List[str] = []
    seen: Set[str] = set()
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        result.append(name)
    return result


def _build_target_counts(day_count: int, attraction_count: int) -> List[int]:
    if day_count <= 0:
        return []

    targets = [1] * day_count
    remaining = max(attraction_count - day_count, 0)

    for idx in range(day_count):
        if remaining <= 0:
            break
        targets[idx] += 1
        remaining -= 1

    for idx in range(day_count):
        if remaining <= 0:
            break
        if targets[idx] < 3:
            targets[idx] += 1
            remaining -= 1

    return targets


def _build_default_theme(day_attractions: List[AttractionInfo], day_index: int) -> str:
    categories = [item.category for item in day_attractions if item.category]
    unique_categories = _dedupe_preserve_order(categories)

    if len(unique_categories) >= 2:
        return f"{unique_categories[0]}与{unique_categories[1]}体验"
    if len(unique_categories) == 1:
        return f"{unique_categories[0]}主题探索"
    return f"第 {day_index} 天轻松游览"


def _build_attraction_prompt_items(attractions: List[AttractionInfo]) -> List[Dict[str, Any]]:
    return [
        {
            "name": item.name,
            "address": item.address,
            "category": item.category,
            "description": item.description,
            "visit_duration": item.visit_duration,
            "suggested_duration": item.suggested_duration,
            "ticket_price": item.ticket_price,
            "ticket_price_note": item.ticket_price_note,
            "rating": item.rating,
            "location": {
                "longitude": item.location.longitude,
                "latitude": item.location.latitude,
            },
        }
        for item in attractions
    ]


def _build_meal_prompt_items(
    meal_candidates: Dict[str, List[MealInfo]]
) -> Dict[str, List[Dict[str, Any]]]:
    result: Dict[str, List[Dict[str, Any]]] = {}
    for slot, meals in meal_candidates.items():
        result[slot] = [
            {
                "meal_type": meal.meal_type,
                "name": meal.name,
                "address": meal.address,
                "description": meal.description,
                "estimated_cost": meal.estimated_cost,
                "category": meal.category,
                "rating": meal.rating,
                "source": meal.source,
            }
            for meal in meals
        ]
    return result


def _extract_selected_names(day: Dict[str, Any]) -> List[str]:
    candidates = [
        day.get("attraction_names"),
        day.get("attractions"),
        day.get("selected_attractions"),
        day.get("poi_names"),
    ]

    for candidate in candidates:
        if not isinstance(candidate, list) or not candidate:
            continue

        if all(isinstance(item, str) and item.strip() for item in candidate):
            return [item.strip() for item in candidate]

        extracted: List[str] = []
        for item in candidate:
            if isinstance(item, dict):
                name = item.get("name")
                if isinstance(name, str) and name.strip():
                    extracted.append(name.strip())
        if extracted:
            return extracted

    return []


def _candidate_score(
    candidate: str,
    current_names: List[str],
    attraction_map: Dict[str, AttractionInfo],
    usage_counts: Dict[str, int],
    attraction_order: Dict[str, int],
) -> tuple:
    current_categories = {
        attraction_map[name].category
        for name in current_names
        if name in attraction_map and attraction_map[name].category
    }
    category = attraction_map[candidate].category
    category_penalty = 1 if category and category in current_categories else 0
    return (
        category_penalty,
        usage_counts.get(candidate, 0),
        attraction_order.get(candidate, 10**6),
    )


def _pick_best_candidate(
    candidates: List[str],
    current_names: List[str],
    attraction_map: Dict[str, AttractionInfo],
    usage_counts: Dict[str, int],
    attraction_order: Dict[str, int],
) -> str:
    unique_candidates = _dedupe_preserve_order(candidates)
    return min(
        unique_candidates,
        key=lambda name: _candidate_score(
            name,
            current_names,
            attraction_map,
            usage_counts,
            attraction_order,
        ),
    )


def _rebalance_day_names(
    initial_day_names: List[List[str]],
    attractions: List[AttractionInfo],
) -> List[List[str]]:
    if not initial_day_names:
        return []

    attraction_map = {item.name: item for item in attractions}
    ordered_names = [item.name for item in attractions]
    attraction_order = {name: idx for idx, name in enumerate(ordered_names)}
    cleaned_days: List[List[str]] = []
    seen_global: Set[str] = set()

    for names in initial_day_names:
        cleaned = []
        for name in _dedupe_preserve_order(names):
            if name not in attraction_map or name in seen_global:
                continue
            cleaned.append(name)
            seen_global.add(name)
        cleaned_days.append(cleaned)

    usage_counts: Dict[str, int] = {}
    target_counts = _build_target_counts(len(cleaned_days), len(attractions))

    for names in cleaned_days:
        for name in names:
            usage_counts[name] = usage_counts.get(name, 0) + 1

    for day_index, names in enumerate(cleaned_days):
        target = target_counts[day_index]
        while len(names) > target:
            removed = names.pop()
            usage_counts[removed] = max(usage_counts.get(removed, 1) - 1, 0)

    for day_index, names in enumerate(cleaned_days):
        target = target_counts[day_index]
        while len(names) < target:
            currently_used = {
                name
                for idx, day_names in enumerate(cleaned_days)
                for name in day_names
                if idx != day_index
            }
            available_unique = [
                name
                for name in ordered_names
                if name not in currently_used and name not in names
            ]

            if available_unique:
                chosen = _pick_best_candidate(
                    available_unique, names, attraction_map, usage_counts, attraction_order
                )
            else:
                reusable = [name for name in ordered_names if name not in names]
                if not reusable and ordered_names:
                    reusable = [ordered_names[day_index % len(ordered_names)]]
                if not reusable:
                    break
                chosen = _pick_best_candidate(
                    reusable, names, attraction_map, usage_counts, attraction_order
                )

            names.append(chosen)
            usage_counts[chosen] = usage_counts.get(chosen, 0) + 1

    return cleaned_days


def _fallback_meal_for_slot(
    slot: str,
    day_index: int,
    meal_candidates: Dict[str, List[MealInfo]],
) -> Optional[MealInfo]:
    options = meal_candidates.get(slot, [])
    if not options:
        return None
    return options[(day_index - 1) % len(options)]


def _extract_meal_name(slot_data: Any) -> Optional[str]:
    if isinstance(slot_data, str) and slot_data.strip():
        return slot_data.strip()
    if isinstance(slot_data, dict):
        name = slot_data.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()
    return None


def _resolve_day_meals(
    day_payload: Dict[str, Any],
    day_index: int,
    meal_candidate_map: Dict[str, Dict[str, MealInfo]],
    fallback_candidates: Dict[str, List[MealInfo]],
) -> DayMeals:
    raw_meals = day_payload.get("meals")
    meal_values: Dict[str, Optional[MealInfo]] = {}

    for slot in MEAL_SLOTS:
        meal_name = None
        if isinstance(raw_meals, dict):
            meal_name = _extract_meal_name(raw_meals.get(slot))

        selected = None
        if meal_name:
            selected = meal_candidate_map.get(slot, {}).get(meal_name)

        if not selected:
            selected = _fallback_meal_for_slot(slot, day_index, fallback_candidates)

        meal_values[slot] = selected

    return DayMeals(**meal_values)


def _normalize_estimated_cost(
    raw_value: Any,
    day_attractions: List[AttractionInfo],
    day_meals: DayMeals,
    hotel: HotelInfo,
) -> float:
    try:
        value = _safe_float(raw_value)
        if value >= 0:
            return value
    except Exception:
        pass

    return _compute_estimated_cost(day_attractions, day_meals, hotel)


def _parse_temperature_range(temperature_text: Optional[str]) -> tuple[Optional[int], Optional[int]]:
    if not temperature_text:
        return (None, None)

    numbers = re.findall(r"-?\d+", temperature_text)
    if len(numbers) >= 2:
        return (int(numbers[0]), int(numbers[1]))
    if len(numbers) == 1:
        value = int(numbers[0])
        return (value, value)
    return (None, None)


def _haversine_km(first: AttractionInfo, second: AttractionInfo) -> float:
    lon1 = math.radians(first.location.longitude)
    lat1 = math.radians(first.location.latitude)
    lon2 = math.radians(second.location.longitude)
    lat2 = math.radians(second.location.latitude)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    value = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 6371.0 * 2 * math.asin(math.sqrt(value))


def _route_distance_km(day_attractions: List[AttractionInfo]) -> float:
    if len(day_attractions) < 2:
        return 0.0

    total = 0.0
    for first, second in zip(day_attractions, day_attractions[1:]):
        total += _haversine_km(first, second)
    return total


def _has_bad_weather(weather: Optional[WeatherInfo]) -> bool:
    if not weather:
        return False

    condition = weather.weather
    low, high = _parse_temperature_range(weather.temperature)
    if any(keyword in condition for keyword in ["雨", "雪", "雷", "冰"]):
        return True
    if high is not None and high >= 32:
        return True
    if low is not None and low <= 0:
        return True
    return False


def _estimate_transport_minutes(total_distance_km: float, mode: str, attraction_count: int) -> int:
    if attraction_count <= 1:
        return 25 if "打车" in mode else 35

    if "步行" in mode and "地铁" not in mode and "公交" not in mode:
        speed = 4.5
    elif "打车" in mode:
        speed = 22.0
    else:
        speed = 15.0

    transfer_buffer = max(attraction_count - 1, 1) * 10
    return max(int((total_distance_km / speed) * 60 + transfer_buffer), 15)


def _build_transportation(
    day_index: int,
    day_attractions: List[AttractionInfo],
    weather: Optional[WeatherInfo],
    hotel: Optional[HotelInfo],
) -> TransportationInfo:
    names = [item.name for item in day_attractions]
    total_distance_km = _route_distance_km(day_attractions)
    bad_weather = _has_bad_weather(weather)

    if len(day_attractions) <= 1:
        mode = "打车/步行"
    elif bad_weather or total_distance_km > 12:
        mode = "地铁+打车"
    elif total_distance_km <= 1.5:
        mode = "步行"
    elif total_distance_km <= 6:
        mode = "地铁/公交+步行"
    else:
        mode = "地铁+步行"

    if len(names) == 0:
        route_summary = "当天景点较少，建议围绕酒店周边灵活安排行程。"
    elif len(names) == 1:
        hotel_prefix = f"从酒店前往{names[0]}" if hotel else f"前往{names[0]}"
        route_summary = f"{hotel_prefix}，游览结束后可在周边用餐或返回休息。"
    else:
        route_summary = " → ".join(names)
        route_summary = f"建议按以下顺序游览：{route_summary}"

    tips: List[str] = []
    if len(day_attractions) >= 3:
        tips.append("建议按当前顺序游览，减少折返。")
    if "地铁" in mode or "公交" in mode:
        tips.append("优先错开 7:30-9:00 和 17:30-19:00 的通勤高峰。")
    if "步行" in mode:
        tips.append("当天步行占比更高，建议穿舒适鞋并注意补水。")
    if "打车" in mode:
        tips.append("如遇降雨或返程较晚，优先考虑打车提升体验。")
    if bad_weather:
        tips.append("天气一般，建议准备雨具或根据温度增减衣物。")

    estimated_time = _estimate_transport_minutes(total_distance_km, mode, len(day_attractions))
    if total_distance_km > 0:
        tips.append(f"景点间累计路程约 {total_distance_km:.1f} 公里。")

    return TransportationInfo(
        mode=mode,
        route_summary=route_summary,
        estimated_travel_time_minutes=estimated_time,
        transport_tips=_dedupe_preserve_order(tips),
    )


def _build_fallback_trip_plan(
    request: TripPlanRequest,
    attractions: List[AttractionInfo],
    weather_list: List[WeatherInfo],
    hotel: HotelInfo,
    meal_candidates: Dict[str, List[MealInfo]],
    fallback_reason: str,
) -> TripPlanResponse:
    daily_plan: List[DayPlan] = []
    day_count = len(weather_list)

    if day_count == 0:
        raise ValueError("缺少天气信息，无法构建行程")

    base_per_day = max(1, len(attractions) // day_count) if attractions else 1

    for idx, weather in enumerate(weather_list, start=1):
        start = (idx - 1) * base_per_day
        end = start + base_per_day
        day_attractions = attractions[start:end]

        if not day_attractions and attractions:
            day_attractions = [attractions[(idx - 1) % len(attractions)]]

        day_meals = DayMeals(
            breakfast=_fallback_meal_for_slot("breakfast", idx, meal_candidates),
            lunch=_fallback_meal_for_slot("lunch", idx, meal_candidates),
            dinner=_fallback_meal_for_slot("dinner", idx, meal_candidates),
            snack=_fallback_meal_for_slot("snack", idx, meal_candidates),
        )

        theme = _build_default_theme(day_attractions, idx)
        transportation = _build_transportation(idx, day_attractions, weather, hotel)
        estimated_cost = _compute_estimated_cost(day_attractions, day_meals, hotel)

        daily_plan.append(
            DayPlan(
                day=idx,
                date=weather.date,
                theme=theme,
                attractions=day_attractions,
                meals=day_meals,
                transportation=transportation,
                hotel=hotel,
                weather=weather,
                estimated_cost=estimated_cost,
            )
        )

    total_budget_estimate = sum(day.estimated_cost for day in daily_plan)
    preference_text = "、".join(request.preferences) if request.preferences else "通用旅行偏好"
    summary = (
        f"已为你在 {request.destination} 生成 {len(daily_plan)} 天行程，"
        f"重点结合了你的偏好：{preference_text}。当前返回的是规则回退结果。"
    )

    return TripPlanResponse(
        destination=request.destination,
        total_days=len(daily_plan),
        total_budget_estimate=total_budget_estimate,
        summary=summary,
        daily_plan=daily_plan,
        generation_source="fallback",
        fallback_reason=fallback_reason,
    )


def _convert_llm_result_to_response(
    llm_result: Dict[str, Any],
    request: TripPlanRequest,
    attractions: List[AttractionInfo],
    weather_list: List[WeatherInfo],
    hotel: HotelInfo,
    meal_candidates: Dict[str, List[MealInfo]],
) -> TripPlanResponse:
    if not weather_list:
        raise ValueError("缺少天气信息，无法构建行程")

    expected_dates = [item.date for item in weather_list]
    expected_date_set: Set[str] = set(expected_dates)
    weather_map = {item.date: item for item in weather_list}
    attraction_map = {item.name: item for item in attractions}
    meal_candidate_map = {
        slot: {meal.name: meal for meal in meals} for slot, meals in meal_candidates.items()
    }

    raw_days = _validate_daily_plan_shape(llm_result, expected_dates)
    summary = _validate_summary(llm_result)

    seen_dates: Set[str] = set()
    parsed_days: Dict[str, Dict[str, Any]] = {}

    for idx, day in enumerate(raw_days, start=1):
        date = day.get("date")
        if not isinstance(date, str) or not date.strip():
            raise ValueError(f"第 {idx} 天缺少 date")
        date = date.strip()

        if date not in expected_date_set:
            raise ValueError(f"第 {idx} 天的日期 {date} 不在允许范围内")
        if date in seen_dates:
            raise ValueError(f"日期 {date} 在 LLM 结果中重复出现")
        seen_dates.add(date)

        raw_theme = day.get("theme")
        theme = raw_theme.strip() if isinstance(raw_theme, str) and raw_theme.strip() else ""
        raw_names = _extract_selected_names(day)
        valid_names = [name for name in _dedupe_preserve_order(raw_names) if name in attraction_map]

        parsed_days[date] = {
            "theme": theme,
            "selected_names": valid_names,
            "estimated_cost": day.get("estimated_cost"),
            "meals": day.get("meals"),
        }

    missing_dates = expected_date_set - seen_dates
    if missing_dates:
        raise ValueError(f"LLM 结果缺少日期：{', '.join(sorted(missing_dates))}")

    initial_day_names = [parsed_days[date]["selected_names"] for date in expected_dates]
    balanced_day_names = _rebalance_day_names(initial_day_names, attractions)

    daily_plan: List[DayPlan] = []

    for idx, date in enumerate(expected_dates, start=1):
        day_info = parsed_days[date]
        selected_names = balanced_day_names[idx - 1]
        if not selected_names:
            raise ValueError(f"第 {idx} 天无法匹配到可用景点")

        selected_attractions = [attraction_map[name] for name in selected_names]
        weather = weather_map[date]
        day_meals = _resolve_day_meals(
            {"meals": day_info.get("meals")},
            idx,
            meal_candidate_map,
            meal_candidates,
        )
        theme = day_info["theme"] or _build_default_theme(selected_attractions, idx)
        transportation = _build_transportation(idx, selected_attractions, weather, hotel)
        estimated_cost = _normalize_estimated_cost(
            day_info["estimated_cost"],
            selected_attractions,
            day_meals,
            hotel,
        )

        daily_plan.append(
            DayPlan(
                day=idx,
                date=date,
                theme=theme,
                attractions=selected_attractions,
                meals=day_meals,
                transportation=transportation,
                hotel=hotel,
                weather=weather,
                estimated_cost=estimated_cost,
            )
        )

    total_budget_estimate = sum(day.estimated_cost for day in daily_plan)

    return TripPlanResponse(
        destination=request.destination,
        total_days=len(daily_plan),
        total_budget_estimate=total_budget_estimate,
        summary=summary,
        daily_plan=daily_plan,
        generation_source="llm",
        fallback_reason=None,
    )


def build_trip_plan(
    request: TripPlanRequest,
    attractions: List[AttractionInfo],
    weather_list: List[WeatherInfo],
    hotel: HotelInfo,
    meal_candidates: Dict[str, List[MealInfo]],
) -> TripPlanResponse:
    expected_dates = [item.date for item in weather_list]
    attraction_prompt_items = _build_attraction_prompt_items(attractions)
    meal_prompt_items = _build_meal_prompt_items(meal_candidates)

    system_prompt = """
你是一名专业旅行规划助手。你会根据用户需求、候选景点、候选餐饮、天气信息和酒店信息，输出严格合法的 JSON 行程方案。你必须遵守以下规则：
1. 只能使用给定的日期，daily_plan 天数必须与给定日期数量完全一致。
2. 每个日期必须出现且只能出现一次，不能新增日期，也不能遗漏日期。
3. 景点必须从给定候选景点中选择。
4. 餐饮请尽量从给定候选餐饮中选择，并为每一天返回 breakfast、lunch、dinner，snack 可选。
5. 每一天请尽量返回 attraction_names 字段；如果你返回 attractions，也必须是包含 name 字段的对象数组。
6. estimated_cost 必须是数字，且不能为负数，应综合酒店价格、景点票价、餐饮和基础交通成本做估算。
7. summary 需要自然、简洁，并体现目的地和偏好。
8. 不要输出 Markdown，不要输出代码块，不要附加解释。
返回格式必须是：
{
  "summary": "整体行程总结",
  "daily_plan": [
    {
      "date": "2026-04-01",
      "theme": "当天主题",
      "attraction_names": ["景点A", "景点B"],
      "meals": {
        "breakfast": "早餐店A",
        "lunch": "午餐餐厅B",
        "dinner": "晚餐餐厅C",
        "snack": "小吃D"
      },
      "estimated_cost": 599
    }
  ]
}
"""

    user_prompt = f"""
【用户需求】
{json.dumps({
        "origin": request.origin,
        "destination": request.destination,
        "start_date": request.start_date,
        "end_date": request.end_date,
        "budget": request.budget,
        "preferences": request.preferences,
    }, ensure_ascii=False, indent=2)}

【允许使用的日期】
{json.dumps(expected_dates, ensure_ascii=False, indent=2)}

【候选景点】
{json.dumps(attraction_prompt_items, ensure_ascii=False, indent=2)}

【候选餐饮】
{json.dumps(meal_prompt_items, ensure_ascii=False, indent=2)}

【天气信息】
{json.dumps([item.model_dump() for item in weather_list], ensure_ascii=False, indent=2)}

【酒店信息】
{json.dumps(hotel.model_dump(), ensure_ascii=False, indent=2)}
"""

    try:
        llm_result = chat_json(system_prompt=system_prompt, user_prompt=user_prompt)
        return _convert_llm_result_to_response(
            llm_result=llm_result,
            request=request,
            attractions=attractions,
            weather_list=weather_list,
            hotel=hotel,
            meal_candidates=meal_candidates,
        )
    except Exception as exc:
        fallback_reason = str(exc)
        print(f"[planner_agent] LLM 调用失败，回退到规则版：{fallback_reason}")
        return _build_fallback_trip_plan(
            request=request,
            attractions=attractions,
            weather_list=weather_list,
            hotel=hotel,
            meal_candidates=meal_candidates,
            fallback_reason=fallback_reason,
        )
