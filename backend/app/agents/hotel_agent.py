from typing import Optional

from app.schemas.response import HotelInfo
from app.tools.provider import get_tool_provider


def get_hotel(destination: str, budget: Optional[float]) -> HotelInfo:
    """
    第一版酒店推荐 Agent。

    目前仍然使用规则型推荐，但入口已经通过共享 tool provider 暴露，
    后续可以平滑切换到酒店平台 API 或 MCP 工具，而不需要改动 orchestrator。
    """

    return get_tool_provider().recommend_hotel(destination, budget)
