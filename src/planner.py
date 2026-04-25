"""
Main planning logic for the evacuation support tool.

Planning flow:
1. find vehicle and waiting pickup groups
2. test route reachability and destination feasibility
3. score each reachable option
4. select the best-ranked plan
"""

from src.prioritization import priority_tuple, score_pickup_group
from src.risk_routing import best_destination_path, dijkstra_path, path_metrics
from src.utils import remaining_capacity


def get_vehicle_node(nodes):
    """
    Return the unique vehicle node from scenario data.

    Args:
        nodes: List of node dictionaries

    Returns:
        Vehicle node dictionary
    """
    for node in nodes:
        if node.get("type") == "vehicle":
            return node
    raise ValueError("No vehicle node was found in the scenario data.")


def get_waiting_pickups(nodes):
    """
    Return pickup nodes whose status is still waiting.

    Args:
        nodes: List of node dictionaries

    Returns:
        List of waiting pickup dictionaries
    """
    return [
        node
        for node in nodes
        if node.get("type") == "pickup" and node.get("status", "waiting") == "waiting"
    ]


def get_candidate_destinations(pickup, nodes):
    """
    Return feasible destinations for one pickup group.

    Rules:
    - medical-need group -> hospital only
    - non-medical group -> shelter only
    - destination must have enough remaining capacity

    Args:
        pickup: Pickup-group dictionary
        nodes: List of node dictionaries

    Returns:
        List of feasible destination nodes
    """

    medical_need = bool(pickup.get("special_medical_need", False))
    group_size = int(pickup.get("group_size", 0) or 0)
    candidates = []

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


def evaluate_pickup_groups(graph, nodes):
    """
    Evaluate every waiting pickup group and return detailed plan options.

    Each returned option includes routing metrics, score, and reason text.

    Algorithm Logic:
    1. Try route from vehicle to pickup
    2. Build feasible destination set for that pickup
    3. Try route from pickup to best destination
    4. Compute route totals and scoring fields

    Args:
        graph: Working road graph
        nodes: List of scenario nodes

    Returns:
        List of evaluation dictionaries (reachable and unreachable cases)
    """
    vehicle = get_vehicle_node(nodes)
    pickups = get_waiting_pickups(nodes)
    evaluations = []

    for pickup in pickups:
        # Step 1: check whether vehicle can reach the pickup.
        to_pickup_path, to_pickup_cost = dijkstra_path(graph, vehicle["id"], pickup["id"])
        if not to_pickup_path:
            evaluations.append(
                {
                    "pickup": pickup,
                    "reachable": False,
                    "reason": "Vehicle cannot reach this pickup group under current road conditions.",
                }
            )
            continue

        # Step 2: gather feasible destination nodes.
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

        # Step 3: route pickup -> best feasible destination.
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

        # Step 4: compute route metrics for final scoring/ranking.
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

        # Store full record for ranking table, and for map display.
        evaluation = {
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
        evaluation["priority_tuple"] = priority_tuple(evaluation)
        evaluations.append(evaluation)

    return evaluations


def choose_best_plan(graph, nodes):
    """
    Pick one best reachable option and return ranked results.

    Returns:
    - best option dict (or None if no reachable option)
    - ranked list of all evaluated options

    Base Case:
    - If no pickup option is reachable, return None and raw evaluations
    """
    evaluations = evaluate_pickup_groups(graph, nodes)
    reachable_options = [item for item in evaluations if item.get("reachable")]

    # Base case: nothing reachable under current road/capacity constraints.
    if not reachable_options:
        return None, evaluations

    # Best option is selected using the custom priority tuple rule.
    best = max(reachable_options, key=priority_tuple)
    ranked = sorted(
        evaluations,
        key=lambda item: priority_tuple(item) if item.get("reachable") else (-1, -1, float("-inf"), float("-inf"), -1),
        reverse=True,
    )

    for index, item in enumerate(ranked, start=1):
        item["rank"] = index

    return best, ranked
