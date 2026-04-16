"""Routing utilities built on top of NetworkX shortest-path methods."""

from __future__ import annotations

from typing import Any

import networkx as nx


def is_reachable(graph: nx.Graph, start: str, end: str) -> bool:
    try:
        return nx.has_path(graph, start, end)
    except nx.NetworkXError:
        return False


def shortest_path(graph: nx.Graph, start: str, end: str) -> tuple[list[str], float]:
    try:
        path = nx.shortest_path(graph, start, end, weight="weight")
        cost = float(nx.shortest_path_length(graph, start, end, weight="weight"))
        return path, cost
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return [], float("inf")


def path_metrics(graph: nx.Graph, path: list[str]) -> dict[str, float]:
    if len(path) < 2:
        return {"distance": 0.0, "travel_time": 0.0, "danger_penalty": 0.0, "weight": 0.0}

    distance = 0.0
    travel_time = 0.0
    danger_penalty = 0.0
    weight = 0.0

    for start, end in zip(path[:-1], path[1:]):
        edge = graph[start][end]
        distance += float(edge.get("distance", 0) or 0)
        travel_time += float(edge.get("travel_time", 0) or 0)
        danger_penalty += float(edge.get("danger_penalty", 0) or 0)
        weight += float(edge.get("weight", 0) or 0)

    return {
        "distance": distance,
        "travel_time": travel_time,
        "danger_penalty": danger_penalty,
        "weight": weight,
    }


def best_destination_path(
    graph: nx.Graph,
    pickup_id: str,
    destinations: list[dict[str, Any]],
) -> dict[str, Any] | None:
    best_option: dict[str, Any] | None = None

    for destination in destinations:
        destination_id = destination["id"]
        path, cost = shortest_path(graph, pickup_id, destination_id)
        if not path:
            continue

        metrics = path_metrics(graph, path)
        option = {
            "destination": destination,
            "path": path,
            "cost": cost,
            "metrics": metrics,
        }
        if best_option is None or option["cost"] < best_option["cost"]:
            best_option = option

    return best_option
