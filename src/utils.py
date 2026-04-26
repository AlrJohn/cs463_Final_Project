"""
Shared helper functions for lookups, capacity, and output formatting.
"""


def index_by_id(items):
    """
    Build a dictionary with keys as each item's id.

    Args:
        items: List of dictionaries containing id field

    Returns:
        Dictionary with id as keys
    """
    return {item["id"]: item for item in items}


def remaining_capacity(node):
    """
    Return available capacity for a shelter/hospital node.

    Args:
        node: Shelter or hospital node dictionary

    Returns:
        Integer capacity remaining
    """
    capacity = int(node.get("capacity", 0) or 0)
    occupancy = int(node.get("current_occupancy", 0) or 0)
    return max(capacity - occupancy, 0)


def route_to_text(path, node_lookup):
    """
    Convert node-id path into a readable route string.

    Args:
        path: Ordered node-id list
        node_lookup: Dictionary keyed by node id

    Returns:
        String route such as 'A -> B -> C'
    """
    if not path:
        return "No route available"
    labels = [node_lookup[node_id].get("name", node_id) for node_id in path]
    return " -> ".join(labels)


def format_reasoning(pickup, destination, total_cost, route_time, danger_cost):
    """
    Build plain-language explanation of why the planner chose this option.

    Args:
        pickup: Selected pickup dictionary
        destination: Selected destination dictionary
        total_cost: Combined route cost
        route_time: Combined travel time
        danger_cost: Combined danger contribution

    Returns:
        Explanatory text for UI display
    """
    # Step 1: collect key values used in ranking and routing.
    urgency = int(pickup.get("severity_level", 0) or 0)
    group_size = int(pickup.get("group_size", 0) or 0)
    medical = bool(pickup.get("special_medical_need", False))
    pickup_name = pickup.get("name", pickup.get("id", "This group"))
    destination_name = destination.get("name", destination.get("id", "destination"))

    priority_intro = f"{pickup_name} was selected because the planner ranks reachable groups by medical need first, then severity, then route score and cost."

    detail_parts = [
        f"This group has severity level {urgency}",
        f"contains {group_size} evacuees",
        f"has a combined route cost of {total_cost:.1f}",
        f"an estimated travel time of {route_time:.1f} minutes",
        f"and a danger contribution of {danger_cost:.1f}."
    ]

    if medical:
        destination_reason = f"Because the group has medical needs, the planner sends it to {destination_name}."
    else:
        destination_reason = f"The planner sends the group to {destination_name} based on capacity and the lowest reachable route cost."

    # Step 2: combine explanation.
    return " ".join([priority_intro, " ".join(detail_parts), destination_reason])
