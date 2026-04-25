"""
Graph-construction helpers for the evacuation planner.

This module converts scenario nodes/edges into a working NetworkX graph
that the routing and planning modules can access.
"""

import networkx as nx

from config import (
    DANGER_PENALTIES,
    ROAD_BLOCKED,
    ROUTE_DANGER_WEIGHT,
    ROUTE_TRAVEL_TIME_WEIGHT,
)

def compute_edge_weight(edge):
    """
    Compute weighted edge cost used by using a risk-aware routing logic.

    Weight formula:
    (ROUTE_TRAVEL_TIME_WEIGHT * travel_time) + (ROUTE_DANGER_WEIGHT * danger_penalty)

    Args:
        edge: Edge dictionary from scenario data

    Returns:
        Float edge weight
    """
    # Use stored edge penalty if present, otherwise fallback to status default.
    status = edge.get("status", "open")
    travel_time = float(edge.get("travel_time", 0) or 0)
    stored_penalty = float(edge.get("danger_penalty", 0) or 0)
    penalty = stored_penalty if stored_penalty else float(DANGER_PENALTIES.get(status, 0))
    return (ROUTE_TRAVEL_TIME_WEIGHT * travel_time) + (ROUTE_DANGER_WEIGHT * penalty)


def build_graph(nodes, edges):
    """
    Build a NetworkX graph from scenario nodes and edges.

    Args:
        nodes: List of node dictionaries
        edges: List of edge dictionaries
        
    Returns:
    - graph: nx.Graph with node/edge attributes attached
    - node_lookup: dict with node id as keys

    """
    graph = nx.Graph()
    node_lookup = {node["id"]: node for node in nodes}

    # Step 1: add all nodes.
    for node in nodes:
        graph.add_node(node["id"], **node)

    # Step 2: add traversable edges (skip blocked roads).
    for edge in edges:
        if edge.get("status") == ROAD_BLOCKED:
            continue

        from_node = edge["from_node"]
        to_node = edge["to_node"]
        if from_node not in node_lookup or to_node not in node_lookup:
            continue

        # Attach both raw fields and computed weight for inspection.
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
