"""
Map rendering helpers using Folium.

This module draws:
- node markers
- roads with status colors
- recommended route overlays
"""

import folium

from config import MAP_CENTER, MAP_TILES, MAP_ZOOM, NODE_COLORS, ROAD_COLORS, ROUTE_COLOR, SECOND_ROUTE_COLOR


def node_position(node):
    """
    Args:
        node: Node dictionary with lat/lon keys

    Returns:
        List [latitude, longitude]
    """
    return [float(node["lat"]), float(node["lon"])]


def add_node_markers(map_obj, nodes):
    """
    Add map markers for vehicle, pickup, shelter, and hospital nodes.

    Args:
        map_obj: Folium map object
        nodes: List of node dictionaries
    """
    for node in nodes:
        node_type = node.get("type", "pickup")
        color = NODE_COLORS.get(node_type, "gray")
        popup_lines = [f"<b>{node.get('name', node['id'])}</b>", f"Type: {node_type}"]

        if node_type == "pickup":
            popup_lines.extend(
                [
                    f"Group size: {node.get('group_size', 'N/A')}",
                    f"Severity: {node.get('severity_level', 'N/A')}",
                    f"Medical need: {node.get('special_medical_need', False)}",
                ]
            )
        elif node_type in {"shelter", "hospital"}:
            popup_lines.extend(
                [
                    f"Capacity: {node.get('capacity', 'N/A')}",
                    f"Current occupancy: {node.get('current_occupancy', 'N/A')}",
                ]
            )

        folium.Marker(
            location=node_position(node),
            popup="<br>".join(popup_lines),
            icon=folium.Icon(color=color, icon="info-sign"),
            tooltip=node.get("name", node["id"]),
        ).add_to(map_obj)


def add_edges(map_obj, nodes_lookup, edges):
    """
    Draw all roads and color them by their current status.

    Args:
        map_obj: Folium map object
        nodes_lookup: Dictionary keyed by node id
        edges: List of edge dictionaries
    """
    for edge in edges:
        start = nodes_lookup.get(edge["from_node"])
        end = nodes_lookup.get(edge["to_node"])
        if not start or not end:
            continue

        color = ROAD_COLORS.get(edge.get("status", "open"), "gray")
        line = folium.PolyLine(
            locations=[node_position(start), node_position(end)],
            color=color,
            weight=5,
            opacity=0.8,
            tooltip=(
                f"{edge['id']}: {edge['from_node']} <-> {edge['to_node']} | "
                f"status={edge.get('status', 'open')} | time={edge.get('travel_time', 0)}"
            ),
        )
        line.add_to(map_obj)


def draw_path(map_obj, path, nodes_lookup, color, label):
    """
    Draw one route if the path has at least two nodes.

    Args:
        map_obj: Folium map object
        path: Node-id list
        nodes_lookup: Dictionary keyed by node id
        color: Polyline color string
        label: Tooltip text
    """
    if len(path) < 2:
        return

    coordinates = [node_position(nodes_lookup[node_id]) for node_id in path if node_id in nodes_lookup]
    folium.PolyLine(
        locations=coordinates,
        color=color,
        weight=7,
        opacity=0.95,
        tooltip=label,
    ).add_to(map_obj)


def add_legend(map_obj):
    """
    Attaches static legend HTML to the map canvas.

    Args:
        map_obj: Folium map object
    """
    legend_html = """
    <div style="position: fixed;
                bottom: 30px; left: 30px; width: 220px; z-index:9999; font-size:14px;
                background-color:white; border:2px solid #555; border-radius:6px;
                color:#1f2937; line-height:1.35;
                padding:10px; box-shadow: 2px 2px 8px rgba(0,0,0,0.25);">
        <b>Legend</b><br>
        <span style="color:blue;">&#9679;</span> Vehicle<br>
        <span style="color:red;">&#9679;</span> Pickup group<br>
        <span style="color:green;">&#9679;</span> Shelter<br>
        <span style="color:purple;">&#9679;</span> Hospital<br>
        <hr style="margin:6px 0;">
        <span style="color:gray;">&#9473;</span> Open road<br>
        <span style="color:orange;">&#9473;</span> Dangerous road<br>
        <span style="color:red;">&#9473;</span> Blocked road<br>
        <span style="color:blue;">&#9473;</span> Recommended route
    </div>
    """
    map_obj.get_root().html.add_child(folium.Element(legend_html))


def build_map(nodes, edges, best_plan=None):
    """
    Build and return the full scenario map used in the Streamlit app.

    Args:
        nodes: List of node dictionaries
        edges: List of edge dictionaries
        best_plan: Optional selected plan dictionary

    Returns:
        Folium map object
    """
    map_obj = folium.Map(location=MAP_CENTER, zoom_start=MAP_ZOOM, tiles=MAP_TILES)
    nodes_lookup = {node["id"]: node for node in nodes}

    # Step 1: draw static scenario elements.
    add_edges(map_obj, nodes_lookup, edges)
    add_node_markers(map_obj, nodes)

    # Step 2: if a recommendation exists, draw route paths.
    if best_plan:
        draw_path(
            map_obj,
            best_plan.get("to_pickup_path", []),
            nodes_lookup,
            ROUTE_COLOR,
            "Vehicle to pickup",
        )
        draw_path(
            map_obj,
            best_plan.get("to_destination_path", []),
            nodes_lookup,
            SECOND_ROUTE_COLOR,
            "Pickup to destination",
        )

    # Step 3: include legend for road/node colors.
    add_legend(map_obj)
    return map_obj
