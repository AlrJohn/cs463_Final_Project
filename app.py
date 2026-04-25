"""
One-page Streamlit app for evacuation route and group-priority planning.

Main UI flow:
1. load scenario data and session state
2. let user update road conditions
3. run planner to compute best pickup+destination
4. render map, metrics, and ranking tables
"""

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from config import APP_SUBTITLE, APP_TITLE, ROAD_STATUSES
from src.data_loader import (
    edges_to_dataframe,
    load_edges,
    load_metadata,
    load_nodes,
    nodes_to_dataframe,
    pickups_to_dataframe,
    shelters_to_dataframe,
)
from src.graph_builder import build_graph
from src.map_view import build_map
from src.planner import choose_best_plan
from src.state_manager import get_edges, initialize_state, reset_edges, save_plan_result, update_edge_status
from src.utils import format_reasoning, route_to_text


st.set_page_config(page_title=APP_TITLE, layout="wide")


@st.cache_data
def load_static_data():
    """
    Load immutable scenario files once and cache them.

    Returns:
        Tuple (nodes, edges, metadata)
    """
    nodes = load_nodes()
    edges = load_edges()
    metadata = load_metadata()
    return nodes, edges, metadata


def build_rankings_table(rankings):
    """
    Convert planner ranking dicts into a display DataFrame.

    Args:
        rankings: List of planner evaluation dictionaries

    Returns:
        Pandas DataFrame for the ranking table UI
    """
    rows = []

    for item in rankings:
        pickup = item.get("pickup", {})
        destination = item.get("destination", {})

        row = {
            "Rank": item.get("rank") if item.get("reachable") else None,
            "Pickup Group": pickup.get("name", pickup.get("id", "N/A")),
            "Reachable": item.get("reachable", False),
            "Destination": destination.get("name", "N/A") if item.get("reachable") else "N/A",
            "Medical Need": pickup.get("special_medical_need", False) if item.get("reachable") else None,
            "Severity": pickup.get("severity_level", None) if item.get("reachable") else None,
            "Score": round(item.get("score", 0), 2) if item.get("reachable") else None,
            "Total Route Cost": round(item.get("total_route_cost", 0), 2) if item.get("reachable") else None,
            "Travel Time": round(item.get("total_route_time", 0), 2) if item.get("reachable") else None,
            "Danger": round(item.get("total_danger", 0), 2) if item.get("reachable") else None,
            "Reason": item.get("reason", ""),
        }
        rows.append(row)

    return pd.DataFrame(rows)


def main():
    """
    Render the full Streamlit evacuation-planning interface.

    UI Flow:
    1. Load data and session state
    2. Apply road status updates
    3. Run planner when requested
    4. Render map, recommended plan, and detail tables
    """
    # Step 1: load static data and initialize session state.
    nodes, default_edges, metadata = load_static_data()
    initialize_state(default_edges)
    edges = get_edges()

    # Step 2: page heading and scenario context.
    st.title(APP_TITLE)
    st.caption(APP_SUBTITLE)

    st.sidebar.header("Scenario Controls")
    st.sidebar.markdown(f"**Scenario:** {metadata.get('name', 'MVP Scenario')}")
    st.sidebar.markdown(f"**Region:** {metadata.get('region', 'Not specified')}")
    st.sidebar.markdown(metadata.get("description", ""))

    # Step 3: road-status controls.
    edge_options = {
        f"{edge['id']} | {edge['from_node']} <-> {edge['to_node']}": edge["id"] for edge in edges
    }
    selected_label = st.sidebar.selectbox("Select a road to update", list(edge_options.keys()))
    selected_edge_id = edge_options[selected_label]

    current_edge = next(edge for edge in edges if edge["id"] == selected_edge_id)
    st.sidebar.markdown(
        "\n".join(
            [
                f"**Current status:** `{current_edge['status']}`",
                f"**Travel time:** {current_edge['travel_time']}",
                f"**Distance:** {current_edge['distance']}",
            ]
        )
    )

    new_status = st.sidebar.radio("New road status", ROAD_STATUSES, index=ROAD_STATUSES.index(current_edge["status"]))

    col_apply, col_reset = st.sidebar.columns(2)
    with col_apply:
        if st.button("Apply road update", use_container_width=True):
            update_edge_status(selected_edge_id, new_status)
            st.success(f"Updated {selected_edge_id} to {new_status}.")
    with col_reset:
        if st.button("Reset roads", use_container_width=True):
            reset_edges()
            st.rerun()

    # Step 4: run planner on demand.
    if st.sidebar.button("Run Planner", type="primary", use_container_width=True):
        graph, _ = build_graph(nodes, get_edges())
        best_plan, rankings = choose_best_plan(graph, nodes)
        save_plan_result(best_plan, rankings)

    best_plan = st.session_state.get("plan_result")
    rankings = st.session_state.get("plan_rankings", [])

    # Step 5: map + result summary layout.
    map_col, results_col = st.columns([1.55, 1], gap="large")

    with map_col:
        st.subheader("Scenario Map")
        folium_map = build_map(nodes, get_edges(), best_plan)
        st_folium(folium_map, width=None, height=650)

    with results_col:
        st.subheader("Planner Output")
        if best_plan:
            pickup = best_plan["pickup"]
            destination = best_plan["destination"]

            st.metric("Recommended Pickup Group", pickup["name"])
            st.metric("Destination", destination["name"])

            metric_a, metric_b = st.columns(2)
            metric_a.metric("Total Route Cost", f"{best_plan['total_route_cost']:.1f}")
            metric_b.metric("Travel Time", f"{best_plan['total_route_time']:.1f} min")

            metric_c, metric_d = st.columns(2)
            metric_c.metric("Danger Score", f"{best_plan['total_danger']:.1f}")
            metric_d.metric("Distance", f"{best_plan['total_distance']:.1f}")

            st.markdown("**Vehicle -> Pickup**")
            st.write(route_to_text(best_plan["to_pickup_path"], {node["id"]: node for node in nodes}))
            st.markdown("**Pickup -> Destination**")
            st.write(route_to_text(best_plan["to_destination_path"], {node["id"]: node for node in nodes}))

            explanation = format_reasoning(
                pickup=pickup,
                destination=destination,
                total_cost=best_plan["total_route_cost"],
                route_time=best_plan["total_route_time"],
                danger_cost=best_plan["total_danger"],
            )
            st.info(explanation)
        else:
            st.warning("Run the planner to generate the current recommendation.")

    # Step 6: detail tables.
    st.divider()

    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("Pickup Groups")
        st.dataframe(pickups_to_dataframe(nodes), use_container_width=True, hide_index=True)

        st.subheader("Road Status Table")
        road_df = edges_to_dataframe(get_edges())[["id", "label", "status", "distance", "travel_time", "danger_penalty"]]
        st.dataframe(road_df, use_container_width=True, hide_index=True)

    with right:
        st.subheader("Shelters and Hospital")
        st.dataframe(shelters_to_dataframe(nodes), use_container_width=True, hide_index=True)

        st.subheader("Group Ranking")
        if rankings:
            st.dataframe(build_rankings_table(rankings), use_container_width=True, hide_index=True)
        else:
            st.caption("No rankings yet. Run the planner after setting road conditions.")

    with st.expander("Scenario Data Preview"):
        node_df = nodes_to_dataframe(nodes)
        st.markdown("**Nodes**")
        st.dataframe(node_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
