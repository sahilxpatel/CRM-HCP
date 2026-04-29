import json
import re
from datetime import date, datetime
from typing import Any, Optional

_TIME_WORDS = {
    "today",
    "yesterday",
    "tomorrow",
    "recent",
    "last",
    "week",
    "month",
    "year",
}


def extract_json(text: str) -> Optional[Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
        match = re.search(r"\[.*\]", text, re.S)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
        return None


def coerce_date(value: Any) -> Optional[date]:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def clean_hcp_name(name: Optional[str]) -> Optional[str]:
    if not name:
        return name
    cleaned = re.sub(r"\s+", " ", name).strip()
    tokens = cleaned.split(" ")
    while tokens and tokens[-1].lower().strip(".,") in _TIME_WORDS:
        tokens = tokens[:-1]
    return " ".join(tokens).strip() if tokens else cleaned


