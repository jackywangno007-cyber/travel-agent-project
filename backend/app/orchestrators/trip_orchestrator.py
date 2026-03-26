from app.agents.attraction_agent import get_attractions
from app.agents.hotel_agent import get_hotel
from app.agents.meal_agent import ensure_day_meals, get_meal_candidates, meal_cost
from app.agents.planner_agent import build_trip_plan
from app.agents.weather_agent import get_weather
from app.schemas.request import RegenerateDayRequest, TripPlanRequest
from app.schemas.response import DayPlan, TripPlanResponse
from app.utils.date_utils import build_date_range


def _normalize_trip_plan_meals(
    trip_plan: TripPlanResponse,
    request: TripPlanRequest,
    meal_candidates,
) -> TripPlanResponse:
    total_budget = 0.0

    for day in trip_plan.daily_plan:
        day.meals = ensure_day_meals(
            meals=day.meals,
            destination=request.destination,
            day_index=day.day,
            meal_candidates=meal_candidates,
        )

        hotel_cost = day.hotel.price_per_night if day.hotel else 0.0
        ticket_cost = sum(item.ticket_price or 0 for item in day.attractions)
        current_meal_cost = meal_cost(day.meals)
        other_cost = max(day.estimated_cost - hotel_cost - ticket_cost - current_meal_cost, 0)

        day.estimated_cost = hotel_cost + ticket_cost + current_meal_cost + other_cost
        total_budget += day.estimated_cost

    trip_plan.total_budget_estimate = total_budget
    return trip_plan


def generate_trip_plan(request: TripPlanRequest) -> TripPlanResponse:
    """
    编排器：
    1. 获取景点
    2. 获取天气
    3. 获取酒店
    4. 获取餐饮候选
    5. 交给 Planner Agent 汇总为完整旅行计划
    6. 在返回前再做一次 meals 和预算规范化，确保前端链路稳定
    """

    dates = build_date_range(request.start_date, request.end_date)

    attractions = get_attractions(
        destination=request.destination,
        preferences=request.preferences,
    )

    weather_list = get_weather(
        destination=request.destination,
        dates=dates,
    )

    hotel = get_hotel(
        destination=request.destination,
        budget=request.budget,
    )

    meal_candidates = get_meal_candidates(
        destination=request.destination,
    )

    trip_plan = build_trip_plan(
        request=request,
        attractions=attractions,
        weather_list=weather_list,
        hotel=hotel,
        meal_candidates=meal_candidates,
    )

    return _normalize_trip_plan_meals(
        trip_plan=trip_plan,
        request=request,
        meal_candidates=meal_candidates,
    )


def regenerate_trip_day(request: RegenerateDayRequest) -> DayPlan:
    trip_plan = request.trip_plan
    current_day = next((day for day in trip_plan.daily_plan if day.day == request.day), None)
    if current_day is None:
        raise ValueError(f"未找到 Day {request.day} 的行程")

    effective_preferences = list(request.preferences)
    if request.guidance:
        effective_preferences.append(request.guidance)

    if not effective_preferences:
        effective_preferences = [
            attraction.category
            for attraction in current_day.attractions
            if attraction.category
        ]

    pseudo_request = TripPlanRequest(
        origin=trip_plan.destination,
        destination=trip_plan.destination,
        start_date=current_day.date,
        end_date=current_day.date,
        budget=current_day.estimated_cost,
        preferences=effective_preferences,
    )

    attractions = get_attractions(
        destination=trip_plan.destination,
        preferences=effective_preferences,
    )

    used_by_other_days = {
        attraction.name
        for day in trip_plan.daily_plan
        if day.day != request.day
        for attraction in day.attractions
    }
    filtered_attractions = [item for item in attractions if item.name not in used_by_other_days]
    if len(filtered_attractions) >= 2:
        attractions = filtered_attractions

    weather_list = [current_day.weather] if current_day.weather else get_weather(
        destination=trip_plan.destination,
        dates=[current_day.date],
    )

    hotel = current_day.hotel or get_hotel(
        destination=trip_plan.destination,
        budget=current_day.estimated_cost,
    )

    meal_candidates = get_meal_candidates(destination=trip_plan.destination)

    regenerated = build_trip_plan(
        request=pseudo_request,
        attractions=attractions,
        weather_list=weather_list,
        hotel=hotel,
        meal_candidates=meal_candidates,
    )

    regenerated = _normalize_trip_plan_meals(
        trip_plan=regenerated,
        request=pseudo_request,
        meal_candidates=meal_candidates,
    )

    new_day = regenerated.daily_plan[0]
    new_day.day = current_day.day
    new_day.date = current_day.date
    new_day.hotel = hotel
    new_day.weather = weather_list[0] if weather_list else current_day.weather
    return new_day
