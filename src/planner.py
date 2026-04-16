"""Main planning logic for the evacuation support tool."""

from __future__ import annotations

from typing import Any

from src.prioritization import score_pickup_group
from src.routing import best_destination_path, path_metrics, shortest_path
from src.utils import remaining_capacity


PlanResult = dict[str, Any]


def get_vehicle_node(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    for node in nodes:
        if node.get("type") == "vehicle":
            return node
    raise ValueError("No vehicle node was found in the scenario data.")


def get_waiting_pickups(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        node
        for node in nodes
        if node.get("type") == "pickup" and node.get("status", "waiting") == "waiting"
    ]


def get_candidate_destinations(
    pickup: dict[str, Any],
    nodes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    medical_need = bool(pickup.get("special_medical_need", False))
    group_size = int(pickup.get("group_size", 0) or 0)
    candidates: list[dict[str, Any]] = []

    for node in nodes:
        node_type = node.get("type")
        if medical_need and node_type != "hospital":
            continue
        if not medical_need and node_type != "shelter":
            continue
        if remaining_capacity(node) < group_size:
            continue
        candidates.append(node)

    return candidates


def evaluate_pickup_groups(graph, nodes: list[dict[str, Any]]) -> list[PlanResult]:
    vehicle = get_vehicle_node(nodes)
    pickups = get_waiting_pickups(nodes)
    evaluations: list[PlanResult] = []

    for pickup in pickups:
        to_pickup_path, to_pickup_cost = shortest_path(graph, vehicle["id"], pickup["id"])
        if not to_pickup_path:
            evaluations.append(
                {
                    "pickup": pickup,
                    "reachable": False,
                    "reason": "Vehicle cannot reach this pickup group under current road conditions.",
                }
            )
            continue

        destinations = get_candidate_destinations(pickup, nodes)
        if not destinations:
            evaluations.append(
                {
                    "pickup": pickup,
                    "reachable": False,
                    "reason": "No destination with enough capacity is available for this group.",
                }
            )
            continue

        destination_option = best_destination_path(graph, pickup["id"], destinations)
        if destination_option is None:
            evaluations.append(
                {
                    "pickup": pickup,
                    "reachable": False,
                    "reason": "The pickup group is cut off from all valid destinations.",
                }
            )
            continue

        pickup_metrics = path_metrics(graph, to_pickup_path)
        destination_metrics = destination_option["metrics"]
        total_route_cost = float(to_pickup_cost + destination_option["cost"])
        total_route_time = pickup_metrics["travel_time"] + destination_metrics["travel_time"]
        total_danger = pickup_metrics["danger_penalty"] + destination_metrics["danger_penalty"]
        total_distance = pickup_metrics["distance"] + destination_metrics["distance"]

        score = score_pickup_group(
            pickup=pickup,
            total_route_cost=total_route_cost,
            destination=destination_option["destination"],
        )

        evaluations.append(
            {
                "pickup": pickup,
                "destination": destination_option["destination"],
                "reachable": True,
                "to_pickup_path": to_pickup_path,
                "to_destination_path": destination_option["path"],
                "to_pickup_metrics": pickup_metrics,
                "to_destination_metrics": destination_metrics,
                "total_route_cost": total_route_cost,
                "total_route_time": total_route_time,
                "total_danger": total_danger,
                "total_distance": total_distance,
                "score": score,
                "reason": "Reachable with current roads and destination capacity.",
            }
        )

    return evaluations


def choose_best_plan(graph, nodes: list[dict[str, Any]]) -> tuple[PlanResult | None, list[PlanResult]]:
    evaluations = evaluate_pickup_groups(graph, nodes)
    reachable_options = [item for item in evaluations if item.get("reachable")]

    if not reachable_options:
        return None, evaluations

    best = max(reachable_options, key=lambda item: item["score"])
    return best, sorted(
        evaluations,
        key=lambda item: item.get("score", float("-inf")),
        reverse=True,
    )
