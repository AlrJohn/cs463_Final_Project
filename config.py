"""Global configuration for the evacuation planner app."""

from __future__ import annotations

# Edge status values
ROAD_OPEN = "open"
ROAD_DANGEROUS = "dangerous"
ROAD_BLOCKED = "blocked"
ROAD_STATUSES = [ROAD_OPEN, ROAD_DANGEROUS, ROAD_BLOCKED]

# Danger penalties used when building the weighted graph.
DANGER_PENALTIES = {
    ROAD_OPEN: 0,
    ROAD_DANGEROUS: 15,
    ROAD_BLOCKED: float("inf"),
}

# Prioritization weights for the greedy group-selection rule.
SEVERITY_MULTIPLIER = 20
GROUP_SIZE_MULTIPLIER = 2
LOW_REMAINING_CAPACITY_PENALTY = 8

# Map display settings
MAP_CENTER = [32.3415, 36.1905]
MAP_ZOOM = 14
MAP_TILES = "OpenStreetMap"

NODE_COLORS = {
    "vehicle": "blue",
    "pickup": "red",
    "shelter": "green",
    "hospital": "purple",
}

ROAD_COLORS = {
    ROAD_OPEN: "gray",
    ROAD_DANGEROUS: "orange",
    ROAD_BLOCKED: "red",
}

ROUTE_COLOR = "blue"
SECOND_ROUTE_COLOR = "darkblue"

# Streamlit display helpers
APP_TITLE = "Evacuation Route and Priority Planner"
APP_SUBTITLE = (
    "A graph-based decision-support tool that balances safety and speed "
    "under changing road conditions."
)
