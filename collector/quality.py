from __future__ import annotations
from statistics import median

def estimate(previous: dict | None, current: dict, threshold: float = 50) -> tuple[float | None, str]:
    if not previous:
        return None, "missing"
    if previous.get("balance_unit") != current.get("balance_unit"):
        return None, "unit_changed"
    if current.get("balance_value") is None or previous.get("balance_value") is None:
        return None, "missing"
    delta = previous["balance_value"] - current["balance_value"]
    if delta < 0:
        return None, "recharge_suspected"
    if delta > threshold:
        return None, "outlier"
    return delta, "ok"

def predicted_days(consumptions: list[float]) -> float | None:
    valid = [x for x in consumptions if x is not None and x >= 0]
    if len(valid) < 5 or median(valid) <= 0:
        return None
    return median(valid)

def coverage(successful: int, total: int) -> float:
    return round(successful / total, 4) if total else 0

def gate(value: float) -> str:
    if value >= .98: return "healthy"
    if value >= .90: return "partial"
    return "blocked"
