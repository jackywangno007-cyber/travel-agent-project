from fastapi import APIRouter

from app.orchestrators.trip_orchestrator import generate_trip_plan, regenerate_trip_day
from app.schemas.request import RegenerateDayRequest, TripPlanRequest
from app.schemas.response import DayPlan, TripPlanResponse

router = APIRouter(prefix="/api/trip", tags=["trip"])


@router.post("/plan", response_model=TripPlanResponse)
def plan_trip(request: TripPlanRequest) -> TripPlanResponse:
    return generate_trip_plan(request)


@router.post("/regenerate-day", response_model=DayPlan)
def regenerate_day(request: RegenerateDayRequest) -> DayPlan:
    return regenerate_trip_day(request)
