import re
from typing import List

from app.schemas.response import ParsedPreferences
from app.services.llm_service import chat_json


INTEREST_RULES = {
    "历史": ["历史", "博物馆", "文化", "古迹", "古城", "遗址", "museum", "history"],
    "美食": ["美食", "吃", "小吃", "本地菜", "探店", "food", "eat"],
    "拍照": ["拍照", "出片", "摄影", "打卡", "photo", "photography"],
    "自然": ["自然", "风景", "山水", "公园", "海边", "lake", "mountain"],
    "艺术": ["艺术", "美术馆", "展览", "画廊", "gallery", "art"],
}

SCENE_RULES = {
    "夜景": ["夜景", "夜游", "夜市", "夜晚"],
    "海边": ["海边", "海景", "海岛", "海滩", "滨海"],
    "古镇": ["古镇", "老街", "古城", "古村"],
    "城市漫游": ["城市漫游", "citywalk", "city walk", "压马路", "街区"],
}

PACE_RULES = {
    "轻松": ["轻松", "休闲", "慢一点", "不赶", "慢游"],
    "紧凑": ["紧凑", "充实", "多逛", "高效"],
}

MOBILITY_RULES = {
    "少走路": ["少走路", "不想太累", "轻松一点", "少步行", "懒一点"],
    "可接受步行": ["多走走", "步行", "citywalk", "暴走"],
}

GROUP_RULES = {
    "情侣": ["情侣", "约会", "二人", "两个人"],
    "亲子": ["亲子", "带娃", "小朋友", "家庭出游"],
    "朋友": ["朋友", "同学", "闺蜜", "兄弟"],
    "独自旅行": ["独自", "一个人", "solo", "独行"],
}


def _normalize_list(value: object) -> List[str]:
    if not isinstance(value, list):
        return []

    result: List[str] = []
    seen = set()
    for item in value:
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _match_first(text: str, rules: dict[str, List[str]]) -> str | None:
    lowered = text.lower()
    for label, keywords in rules.items():
        if any(keyword.lower() in lowered for keyword in keywords):
            return label
    return None


def _match_many(text: str, rules: dict[str, List[str]]) -> List[str]:
    lowered = text.lower()
    result: List[str] = []
    for label, keywords in rules.items():
        if any(keyword.lower() in lowered for keyword in keywords):
            result.append(label)
    return result


def _fallback_parse_preferences(raw_preferences: List[str]) -> ParsedPreferences:
    merged_text = "，".join(item.strip() for item in raw_preferences if item.strip())
    return ParsedPreferences(
        interests=_match_many(merged_text, INTEREST_RULES),
        pace=_match_first(merged_text, PACE_RULES),
        mobility=_match_first(merged_text, MOBILITY_RULES),
        scene=_match_many(merged_text, SCENE_RULES),
        group_type=_match_first(merged_text, GROUP_RULES),
    )


def _sanitize_llm_result(result: dict) -> ParsedPreferences:
    pace = result.get("pace")
    mobility = result.get("mobility")
    group_type = result.get("group_type")

    return ParsedPreferences(
        interests=_normalize_list(result.get("interests")),
        pace=pace.strip() if isinstance(pace, str) and pace.strip() else None,
        mobility=mobility.strip() if isinstance(mobility, str) and mobility.strip() else None,
        scene=_normalize_list(result.get("scene")),
        group_type=group_type.strip() if isinstance(group_type, str) and group_type.strip() else None,
    )


def parse_preferences(raw_preferences: List[str]) -> ParsedPreferences:
    merged_text = "，".join(item.strip() for item in raw_preferences if item.strip())
    if not merged_text:
        return ParsedPreferences()

    system_prompt = """
你是一个旅行偏好解析器。你的任务是把用户的自然语言旅行偏好解析成结构化 JSON。
只返回合法 JSON，不要输出解释。
返回格式必须为：
{
  "interests": ["历史", "美食", "拍照"],
  "pace": "轻松",
  "mobility": "少走路",
  "scene": ["夜景", "海边"],
  "group_type": "情侣"
}
要求：
1. interests 和 scene 必须是字符串数组，没有则返回空数组。
2. pace / mobility / group_type 没有明确提及时返回 null。
3. 标签尽量使用简洁中文，例如：历史、美食、拍照、自然、艺术、夜景、海边、情侣、亲子、轻松、少走路。
4. 不要臆造用户没提到的偏好。
"""

    user_prompt = f"用户偏好原文：{merged_text}"

    try:
        result = chat_json(system_prompt=system_prompt, user_prompt=user_prompt)
        parsed = _sanitize_llm_result(result)
        if (
            not parsed.interests
            and not parsed.scene
            and not parsed.pace
            and not parsed.mobility
            and not parsed.group_type
        ):
            return _fallback_parse_preferences(raw_preferences)
        return parsed
    except Exception as exc:
        print(f"[preference_parser] LLM 偏好解析失败，回退到规则解析：{exc}")
        return _fallback_parse_preferences(raw_preferences)


def build_preference_tags(parsed: ParsedPreferences, raw_preferences: List[str]) -> List[str]:
    merged_text = "，".join(item.strip() for item in raw_preferences if item.strip())
    fallback_tokens = [
        token.strip()
        for token in re.split(r"[，,、/；;\s]+", merged_text)
        if token.strip()
    ]

    ordered_tags: List[str] = []
    for value in [
        *parsed.interests,
        parsed.pace,
        parsed.mobility,
        *parsed.scene,
        parsed.group_type,
        *fallback_tokens,
    ]:
        if value and value not in ordered_tags:
            ordered_tags.append(value)

    return ordered_tags
