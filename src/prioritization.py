"""
Greedy scoring and ranking helpers for pickup-group prioritization.

This module separates:
- numeric score calculation
- tie-break ordering rule
"""

from config import GROUP_SIZE_MULTIPLIER, LOW_REMAINING_CAPACITY_PENALTY, SEVERITY_MULTIPLIER
from src.utils import remaining_capacity


def score_pickup_group(pickup, total_route_cost, destination):
    """
    Return the numeric score for one reachable pickup option.

    Score formula:
        (severity * SEVERITY_MULTIPLIER) + (group_size * GROUP_SIZE_MULTIPLIER)
      - total_route_cost
      - optional low-capacity penalty

    Args:
        pickup: Pickup-group dictionary
        total_route_cost: Combined vehicle->pickup and pickup->destination cost
        destination: Destination node dictionary

    Returns:
        Float score (higher is better)
    """
    # Step 1: collect group and destination values.
    severity = int(pickup.get("severity_level", 0) or 0)
    group_size = int(pickup.get("group_size", 0) or 0)
    capacity_left = remaining_capacity(destination)

    # Step 2: apply capacity safety penalty when destination is very tight.
    shelter_penalty = LOW_REMAINING_CAPACITY_PENALTY if capacity_left < group_size else 0

    # Step 3: compute final score.
    return (severity * SEVERITY_MULTIPLIER) + (group_size * GROUP_SIZE_MULTIPLIER) - total_route_cost - shelter_penalty


def priority_tuple(option):
    """
    Rank reachable options using the agreed project rule.

    Priority order:
    1. medical-need group first
    2. higher severity first
    3. higher overall score
    4. lower total route cost
    5. larger group size

    Args:
        option: One evaluated reachable option dictionary

    Returns:
        Tuple used directly in Python max/sorted ranking
    """
    # Extract values once so the tuple stays easy to read and debug.
    pickup = option.get("pickup", {})
    medical_need = 1 if pickup.get("special_medical_need", False) else 0
    severity = int(pickup.get("severity_level", 0) or 0)
    score = float(option.get("score", float("-inf")))
    total_route_cost = float(option.get("total_route_cost", float("inf")))
    group_size = int(pickup.get("group_size", 0) or 0)
    return (medical_need, severity, score, -total_route_cost, group_size)
