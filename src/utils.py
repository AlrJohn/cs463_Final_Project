"""Shared helper functions for formatting and lookups."""

from __future__ import annotations

from typing import Any


def index_by_id(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in items}


def remaining_capacity(node: dict[str, Any]) -> int:
    capacity = int(node.get("capacity", 0) or 0)
    occupancy = int(node.get("current_occupancy", 0) or 0)
    return max(capacity - occupancy, 0)


def route_to_text(path: list[str], node_lookup: dict[str, dict[str, Any]]) -> str:
    if not path:
        return "No route available"
    labels = [node_lookup[node_id].get("name", node_id) for node_id in path]
    return " -> ".join(labels)


def format_reasoning(
    pickup: dict[str, Any],
    destination: dict[str, Any],
    total_cost: float,
    route_time: float,
    danger_cost: float,
) -> str:
    urgency = pickup.get("severity_level", 0)
    group_size = pickup.get("group_size", 0)
    medical = pickup.get("special_medical_need", False)
    destination_name = destination.get("name", destination.get("id", "destination"))

    parts = [
        f"{pickup.get('name', pickup.get('id', 'This group'))} was selected because it remains reachable",
        f"with a combined route cost of {total_cost:.1f}",
        f"an estimated travel time of {route_time:.1f} minutes",
        f"and a danger contribution of {danger_cost:.1f}.",
        f"The group has severity level {urgency} and contains {group_size} evacuees.",
    ]
    if medical:
        parts.append(f"Because the group has medical needs, the planner routes it to {destination_name}.")
    else:
        parts.append(f"The planner sends the group to {destination_name} based on capacity and route cost.")
    return " ".join(parts)
