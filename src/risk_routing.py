"""
Routing utilities for the evacuation planner.

This module implements a Dijkstra-style algorithm
using a min-heap priority queue.
"""

import heapq

import networkx as nx

from config import ROUTE_DANGER_WEIGHT, ROUTE_TRAVEL_TIME_WEIGHT


def compute_edge_cost(edge):
    """
    Compute non-negative edge cost used by Dijkstra.

    Cost formula:
        (ROUTE_TRAVEL_TIME_WEIGHT * travel_time) + (ROUTE_DANGER_WEIGHT * danger_penalty)

    Args:
        edge: Edge attribute dictionary from the graph

    Returns:
        Float cost value used in shortest-path computation
    """
    travel_time = float(edge.get("travel_time", 0) or 0)
    danger_penalty = float(edge.get("danger_penalty", 0) or 0)
    return (ROUTE_TRAVEL_TIME_WEIGHT * travel_time) + (ROUTE_DANGER_WEIGHT * danger_penalty)


def dijkstra_path(graph, start, end):
    """
    Return the minimum-cost path and total cost from start to end.

    Algorithm Logic:
    1. Initialize all node distances to infinity except source (0)
    2. Use a min-heap to always expand the next cheapest node
    3. Relax neighbors and update parent pointers
    4. Reconstruct path from destination back to source

    Base Cases:
    - If start/end is missing: no path
    - If start == end: path is [start] with cost 0

    Args:
        graph: NetworkX graph with edge attributes
        start: Source node id
        end: Destination node id

    Returns:
        Tuple (path_list, total_cost)
    """
    # Base case 1: invalid node ids.
    if start not in graph or end not in graph:
        return [], float("inf")
    # Base case 2: same source and destination.
    if start == end:
        return [start], 0.0

    # Step 1: initialize tracking structures.
    distances = {node: float("inf") for node in graph.nodes}
    previous = {node: None for node in graph.nodes}
    distances[start] = 0.0

    # Min-heap stores (current_distance, node_id)
    queue = [(0.0, start)]

    # Step 2: repeatedly expand the cheapest node
    while queue:
        current_dist, node = heapq.heappop(queue)

        # Skip stale entries from earlier worse paths
        if current_dist > distances[node]:
            continue

        # Early stop when we pop the target with best known cost
        if node == end:
            break

        # Step 3: relax outgoing edges from current node
        for neighbor in graph.neighbors(node):
            edge_data = graph[node][neighbor]
            edge_cost = compute_edge_cost(edge_data)
            new_dist = current_dist + edge_cost

            # Update shortest known path to neighbor when improvement is found
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                previous[neighbor] = node
                heapq.heappush(queue, (new_dist, neighbor))

    # If target still has infinity, there is no reachable path.
    if distances[end] == float("inf"):
        return [], float("inf")

    # Step 4: reconstruct path by traversing parents backward.
    path = []
    curr = end
    while curr is not None:
        path.append(curr)
        curr = previous[curr]
    path.reverse()
    return path, float(distances[end])


def path_metrics(graph, path):
    """
    Gather distance/time/danger/cost totals for a chosen path.

    Args:
        graph: NetworkX graph
        path: Ordered node-id list

    Returns:
        Dictionary with distance, travel_time, danger_penalty, and cost
    """
    if len(path) < 2:
        return {"distance": 0.0, "travel_time": 0.0, "danger_penalty": 0.0, "cost": 0.0}

    distance = 0.0
    travel_time = 0.0
    danger_penalty = 0.0
    cost = 0.0

    for start, end in zip(path[:-1], path[1:]):
        edge = graph[start][end]
        distance += float(edge.get("distance", 0) or 0)
        travel_time += float(edge.get("travel_time", 0) or 0)
        danger_penalty += float(edge.get("danger_penalty", 0) or 0)
        cost += compute_edge_cost(edge)

    return {
        "distance": distance,
        "travel_time": travel_time,
        "danger_penalty": danger_penalty,
        "cost": cost,
    }


def best_destination_path(graph, pickup_id, destinations):
    """
    Find the minimum-cost destination path from pickup_id.

    destinations is already filtered for feasibility (capacity/type constraints).

    Args:
        graph: NetworkX graph
        pickup_id: Node id for pickup group
        destinations: Feasible destination node dictionaries

    Returns:
        Best option dictionary or None if all candidates are unreachable
    """
    best_option = None

    # Evaluate each candidate destination and keep the cheapest reachable option.
    for destination in destinations:
        destination_id = destination["id"]
        path, cost = dijkstra_path(graph, pickup_id, destination_id)
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
