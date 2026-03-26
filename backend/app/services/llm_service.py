import json

from openai import OpenAI

from app.utils.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL


def get_llm_client() -> OpenAI:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY 未配置")

    return OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL if OPENAI_BASE_URL else None,
    )


def _extract_json_text(content: str) -> str:
    text = content.strip()

    if text.startswith("```"):
        lines = text.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    return text


def chat_json(system_prompt: str, user_prompt: str) -> dict:
    client = get_llm_client()

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("模型返回内容为空")

    json_text = _extract_json_text(content)

    try:
        return json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"模型返回的不是合法 JSON：{content}") from exc
