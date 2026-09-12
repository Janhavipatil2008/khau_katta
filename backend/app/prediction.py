"""
Lightweight prediction logic for Khau Katta.

Two jobs:
1. estimate_prep_time(): given the new order's items and how many orders are
   already pending, estimate how long this order will realistically take
   (accounts for kitchen queue load, not just the raw item prep times).
2. rush_level(): given how many orders are currently pending, classify the
   canteen as Low / Medium / High rush.

This starts as a simple, explainable heuristic model (no external ML
dependency needed to run). It's structured so you can later swap
`estimate_prep_time` for a trained regression model (e.g. scikit-learn)
without changing any callers.
"""

from datetime import datetime, timedelta
from typing import List, Tuple

# Assume the kitchen can work on a few items in parallel.
KITCHEN_PARALLELISM = 3
# Each pending order adds this many minutes of queue delay per item ahead of it.
QUEUE_DELAY_PER_PENDING_ORDER = 1.5


def estimate_prep_time(item_prep_times: List[int], pending_orders_count: int) -> int:
    """Returns predicted prep time in minutes for a new order."""
    base_time = max(item_prep_times) if item_prep_times else 5
    queue_delay = (pending_orders_count / KITCHEN_PARALLELISM) * QUEUE_DELAY_PER_PENDING_ORDER
    predicted = base_time + queue_delay
    return max(2, round(predicted))


def pickup_window(predicted_minutes: int) -> Tuple[datetime, datetime]:
    """Returns (window_start, window_end) around the predicted ready time."""
    now = datetime.utcnow()
    ready_at = now + timedelta(minutes=predicted_minutes)
    return ready_at, ready_at + timedelta(minutes=5)


def rush_level(pending_orders_count: int) -> str:
    if pending_orders_count <= 5:
        return "Low"
    if pending_orders_count <= 15:
        return "Medium"
    return "High"


def hourly_forecast(orders_per_hour: dict) -> dict:
    """
    orders_per_hour: {0: 3, 1: 5, ..., 23: 10} — historical avg orders placed
    in each hour of the day. Returns the same hours labeled Low/Medium/High.
    Swap this for a real time-series model once you have enough order history.
    """
    forecast = {}
    for hour, count in orders_per_hour.items():
        forecast[hour] = rush_level(count)
    return forecast
