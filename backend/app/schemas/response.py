from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class Location(BaseModel):
    longitude: float = Field(..., description="经度")
    latitude: float = Field(..., description="纬度")


class AttractionInfo(BaseModel):
    name: str = Field(..., description="景点名称")
    address: str = Field(..., description="景点地址")
    location: Location = Field(..., description="景点坐标")
    description: str = Field(..., description="面向用户的简短景点描述")
    visit_duration: int = Field(..., description="建议游玩时长，单位为分钟")
    suggested_duration: str = Field(..., description="建议游玩时长文本")
    category: Optional[str] = Field(default=None, description="清洗后的展示分类")
    rating: Optional[float] = Field(default=None, description="评分")
    image_url: Optional[str] = Field(default=None, description="景点图片链接")
    ticket_price: Optional[float] = Field(default=None, description="门票价格")
    ticket_price_note: Optional[str] = Field(
        default=None,
        description="门票说明，例如经验估算或免费提示",
    )


class MealInfo(BaseModel):
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"] = Field(
        ...,
        description="餐饮类型",
    )
    name: str = Field(..., description="餐饮名称")
    address: str = Field(..., description="餐饮地址")
    description: str = Field(..., description="简短餐饮描述")
    estimated_cost: float = Field(..., description="餐饮预计花费")
    category: Optional[str] = Field(default=None, description="餐饮分类")
    rating: Optional[float] = Field(default=None, description="餐饮评分")
    source: Literal["poi", "fallback"] = Field(
        default="poi",
        description="数据来源，poi 表示真实搜索，fallback 表示兜底结果",
    )


class DayMeals(BaseModel):
    breakfast: Optional[MealInfo] = Field(default=None, description="早餐安排")
    lunch: Optional[MealInfo] = Field(default=None, description="午餐安排")
    dinner: Optional[MealInfo] = Field(default=None, description="晚餐安排")
    snack: Optional[MealInfo] = Field(default=None, description="加餐或小吃安排")


class TransportationInfo(BaseModel):
    mode: str = Field(..., description="当天主要交通方式")
    route_summary: str = Field(..., description="轻量路线说明")
    estimated_travel_time_minutes: Optional[int] = Field(
        default=None,
        description="当天景点间预计交通耗时，单位分钟",
    )
    transport_tips: List[str] = Field(
        default_factory=list,
        description="当天交通建议或出行提醒",
    )


class HotelInfo(BaseModel):
    name: str = Field(..., description="酒店名称")
    address: str = Field(..., description="酒店地址")
    location: Location = Field(..., description="酒店坐标")
    price_per_night: float = Field(..., description="每晚价格")
    location_summary: str = Field(..., description="酒店位置描述")
    description: str = Field(..., description="面向用户的酒店简短描述")
    price_note: Optional[str] = Field(default=None, description="价格说明，例如经验估算")


class WeatherInfo(BaseModel):
    date: str = Field(..., description="日期")
    weather: str = Field(..., description="天气情况")
    temperature: str = Field(..., description="温度范围")


class DayPlan(BaseModel):
    day: int = Field(..., description="第几天")
    date: str = Field(..., description="日期")
    theme: str = Field(..., description="当天主题")
    attractions: List[AttractionInfo] = Field(default_factory=list, description="当天景点安排")
    meals: DayMeals = Field(default_factory=DayMeals, description="当天餐饮安排")
    transportation: TransportationInfo = Field(..., description="当天交通方式与路线建议")
    hotel: Optional[HotelInfo] = Field(default=None, description="当天酒店")
    weather: Optional[WeatherInfo] = Field(default=None, description="天气信息")
    estimated_cost: float = Field(..., description="当天预计花费")


class TripPlanResponse(BaseModel):
    destination: str = Field(..., description="目的地")
    total_days: int = Field(..., description="总天数")
    total_budget_estimate: float = Field(..., description="总预算预估")
    summary: str = Field(..., description="整体行程总结")
    daily_plan: List[DayPlan] = Field(default_factory=list, description="每日行程安排")
    generation_source: Literal["llm", "fallback"] = Field(
        ...,
        description="结果来源，llm 表示大模型生成，fallback 表示规则回退",
    )
    fallback_reason: Optional[str] = Field(
        default=None,
        description="回退原因，仅在 fallback 时返回",
    )
