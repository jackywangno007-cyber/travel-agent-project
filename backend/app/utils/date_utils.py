from datetime import date, datetime, timedelta
from typing import List


DATE_FORMAT = "%Y-%m-%d"


def parse_iso_date(value: str) -> date:
    try:
        return datetime.strptime(value, DATE_FORMAT).date()
    except ValueError as exc:
        raise ValueError(f"日期格式错误：{value}，应为 YYYY-MM-DD") from exc


def build_date_range(start_date: str, end_date: str) -> List[str]:
    start = parse_iso_date(start_date)
    end = parse_iso_date(end_date)

    if end < start:
        raise ValueError("end_date 不能早于 start_date")

    dates: List[str] = []
    current = start
    while current <= end:
        dates.append(current.isoformat())
        current += timedelta(days=1)

    return dates
