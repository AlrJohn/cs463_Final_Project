"""
Session-state helpers for Streamlit app interaction.

This module manages:
- current road status
- default road snapshot for reset
- last planner result and ranking list
"""

from copy import deepcopy

import streamlit as st

from config import DANGER_PENALTIES

EDGE_STATE_KEY = "edge_state"
DEFAULT_EDGE_STATE_KEY = "default_edge_state"
PLAN_RESULT_KEY = "plan_result"
PLAN_RANKINGS_KEY = "plan_rankings"


def initialize_state(edges):
    """
    Initialize Streamlit state keys once at app startup

    Args:
        edges: Default edge list from scenario data
    """
    if EDGE_STATE_KEY not in st.session_state:
        st.session_state[EDGE_STATE_KEY] = deepcopy(edges)
    if DEFAULT_EDGE_STATE_KEY not in st.session_state:
        st.session_state[DEFAULT_EDGE_STATE_KEY] = deepcopy(edges)
    if PLAN_RESULT_KEY not in st.session_state:
        st.session_state[PLAN_RESULT_KEY] = None
    if PLAN_RANKINGS_KEY not in st.session_state:
        st.session_state[PLAN_RANKINGS_KEY] = []


def get_edges():
    """
    Returns mutable edge list from session state
    """
    return st.session_state[EDGE_STATE_KEY]


def update_edge_status(edge_id, new_status):
    """
    Update one road status and refresh its danger penalty

    Args:
        edge_id: Edge id string
        new_status: New road status string
    """
    for edge in st.session_state[EDGE_STATE_KEY]:
        if edge["id"] == edge_id:
            edge["status"] = new_status
            # Blocked roads are removed from the graph, so we keep penalty 0 in UI state.
            if new_status == "blocked":
                edge["danger_penalty"] = 0
            else:
                edge["danger_penalty"] = float(DANGER_PENALTIES.get(new_status, 0) or 0)
            break


def reset_edges():
    """
    Restore all roads to default state and clear planner outputs.
    """
    st.session_state[EDGE_STATE_KEY] = deepcopy(st.session_state[DEFAULT_EDGE_STATE_KEY])
    st.session_state[PLAN_RESULT_KEY] = None
    st.session_state[PLAN_RANKINGS_KEY] = []


def save_plan_result(best_plan, rankings):
    """
    Save planner outputs to session state for rendering.

    Args:
        best_plan: Best plan dictionary or None
        rankings: List of ranking dictionaries
    """
    st.session_state[PLAN_RESULT_KEY] = best_plan
    st.session_state[PLAN_RANKINGS_KEY] = rankings
