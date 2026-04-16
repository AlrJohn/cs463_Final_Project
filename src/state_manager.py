"""Streamlit session-state helpers."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import streamlit as st


EDGE_STATE_KEY = "edge_state"
DEFAULT_EDGE_STATE_KEY = "default_edge_state"
PLAN_RESULT_KEY = "plan_result"
PLAN_RANKINGS_KEY = "plan_rankings"


def initialize_state(edges: list[dict[str, Any]]) -> None:
    if EDGE_STATE_KEY not in st.session_state:
        st.session_state[EDGE_STATE_KEY] = deepcopy(edges)
    if DEFAULT_EDGE_STATE_KEY not in st.session_state:
        st.session_state[DEFAULT_EDGE_STATE_KEY] = deepcopy(edges)
    if PLAN_RESULT_KEY not in st.session_state:
        st.session_state[PLAN_RESULT_KEY] = None
    if PLAN_RANKINGS_KEY not in st.session_state:
        st.session_state[PLAN_RANKINGS_KEY] = []


def get_edges() -> list[dict[str, Any]]:
    return st.session_state[EDGE_STATE_KEY]


def update_edge_status(edge_id: str, new_status: str) -> None:
    for edge in st.session_state[EDGE_STATE_KEY]:
        if edge["id"] == edge_id:
            edge["status"] = new_status
            if new_status == "open":
                edge["danger_penalty"] = 0
            elif new_status == "dangerous":
                edge["danger_penalty"] = 15
            elif new_status == "blocked":
                edge["danger_penalty"] = 0
            break


def reset_edges() -> None:
    st.session_state[EDGE_STATE_KEY] = deepcopy(st.session_state[DEFAULT_EDGE_STATE_KEY])
    st.session_state[PLAN_RESULT_KEY] = None
    st.session_state[PLAN_RANKINGS_KEY] = []


def save_plan_result(best_plan: dict[str, Any] | None, rankings: list[dict[str, Any]]) -> None:
    st.session_state[PLAN_RESULT_KEY] = best_plan
    st.session_state[PLAN_RANKINGS_KEY] = rankings
