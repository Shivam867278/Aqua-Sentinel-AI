from __future__ import annotations

from typing import Any, Dict, Iterable, Tuple


def parse_float(payload: Dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(payload.get(key, default))
    except (TypeError, ValueError):
        raise ValueError(f"`{key}` must be a number")


def require_fields(payload: Dict[str, Any], fields: Iterable[str]) -> None:
    missing = [field for field in fields if field not in payload]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")


def validate_range(value: float, key: str, bounds: Tuple[float, float]) -> None:
    low, high = bounds
    if value < low or value > high:
        raise ValueError(f"`{key}` must be between {low} and {high}")


def validate_choice(value: str, key: str, choices: Iterable[str]) -> None:
    allowed = set(choices)
    if value not in allowed:
        raise ValueError(f"`{key}` must be one of: {', '.join(sorted(allowed))}")
