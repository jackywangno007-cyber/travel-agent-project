from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from app.schemas.response import TripPlanResponse
from app.utils.date_utils import build_date_range


class TripPlanRequest(BaseModel):
    origin: str = Field(..., description="出发地")
    destination: str = Field(..., description="目的地")
    start_date: str = Field(..., description="出行开始日期，例如 2026-04-01")
    end_date: str = Field(..., description="出行结束日期，例如 2026-04-03")
    budget: Optional[float] = Field(default=None, description="预算，单位元")
    preferences: List[str] = Field(
        default_factory=list,
        description="用户偏好，例如 美食 / 历史 / 拍照",
    )

    @model_validator(mode="after")
    def validate_date_range(self) -> "TripPlanRequest":
        build_date_range(self.start_date, self.end_date)
        return self


class RegenerateDayRequest(BaseModel):
    trip_plan: TripPlanResponse = Field(..., description="当前整份旅行计划")
    day: int = Field(..., ge=1, description="需要重新规划的天数，例如 2 表示 Day 2")
    preferences: List[str] = Field(
        default_factory=list,
        description="单日重规划的补充偏好，例如 更轻松 / 更美食 / 更少步行",
    )
    guidance: Optional[str] = Field(
        default=None,
        description="用户对这一天的额外说明，例如 雨天优先室内 / 想多吃本地菜",
    )

    @model_validator(mode="after")
    def validate_day_range(self) -> "RegenerateDayRequest":
        total_days = len(self.trip_plan.daily_plan)
        if self.day > total_days:
            raise ValueError(f"day 超出范围，当前行程只有 {total_days} 天")
        return self
