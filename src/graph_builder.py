"""Build a working NetworkX graph from scenario data."""

from __future__ import annotations

from typing import Any

import networkx as nx

from config import DANGER_PENALTIES, ROAD_BLOCKED


NodeMap = dict[str, dict[str, Any]]


def compute_edge_weight(edge: dict[str, Any]) -> float:
    status = edge.get("status", "open")
    travel_time = float(edge.get("travel_time", 0) or 0)
    stored_penalty = float(edge.get("danger_penalty", 0) or 0)
    penalty = stored_penalty if stored_penalty else float(DANGER_PENALTIES.get(status, 0))
    return travel_time + penalty


def build_graph(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> tuple[nx.Graph, NodeMap]:
    graph = nx.Graph()
    node_lookup = {node["id"]: node for node in nodes}

    for node in nodes:
        graph.add_node(node["id"], **node)

    for edge in edges:
        if edge.get("status") == ROAD_BLOCKED:
            continue

        from_node = edge["from_node"]
        to_node = edge["to_node"]
        if from_node not in node_lookup or to_node not in node_lookup:
            continue

        graph.add_edge(
            from_node,
            to_node,
            id=edge["id"],
            distance=float(edge.get("distance", 0) or 0),
            travel_time=float(edge.get("travel_time", 0) or 0),
            status=edge.get("status", "open"),
            danger_penalty=float(edge.get("danger_penalty", 0) or 0),
            weight=compute_edge_weight(edge),
        )

    return graph, node_lookup
