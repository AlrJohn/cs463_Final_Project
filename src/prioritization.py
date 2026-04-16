"""Greedy scoring for selecting the next pickup group."""

from __future__ import annotations

from typing import Any

from config import GROUP_SIZE_MULTIPLIER, LOW_REMAINING_CAPACITY_PENALTY, SEVERITY_MULTIPLIER
from src.utils import remaining_capacity


def score_pickup_group(
    pickup: dict[str, Any],
    total_route_cost: float,
    destination: dict[str, Any],
) -> float:
    severity = int(pickup.get("severity_level", 0) or 0)
    group_size = int(pickup.get("group_size", 0) or 0)
    capacity_left = remaining_capacity(destination)

    shelter_penalty = LOW_REMAINING_CAPACITY_PENALTY if capacity_left < group_size else 0

    return (severity * SEVERITY_MULTIPLIER) + (group_size * GROUP_SIZE_MULTIPLIER) - total_route_cost - shelter_penalty
