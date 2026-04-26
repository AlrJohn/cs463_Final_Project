"""
Data loading and table-conversion helpers for the evacuation app.

This module handles:
- reading JSON scenario files
- converting node/edge data into DataFrames for UI display
"""

import json
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"


def read_json(path):
    """
    Read a JSON file and return parsed Python data.

    Args:
        path: pathlib Path object

    Returns:
        Parsed JSON object (dict or list)
    """
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_nodes():
    """
    Load all scenario nodes from data/nodes.json.

    Returns:
        List of node dictionaries
    """
    return list(read_json(DATA_DIR / "nodes.json"))


def load_edges():
    """
    Load all scenario edges from data/edges.json.

    Returns:
        List of edge dictionaries
    """
    return list(read_json(DATA_DIR / "edges.json"))


def load_metadata():
    """
    Load scenario metadata from data/scenario_metadata.json.

    Returns:
        Metadata dictionary
    """
    metadata = read_json(DATA_DIR / "scenario_metadata.json")
    if not isinstance(metadata, dict):
        raise ValueError("Scenario metadata must be a JSON object.")
    return metadata


def nodes_to_dataframe(nodes):
    """
    Convert node list to DataFrame for preview tables.

    Args:
        nodes: List of node dictionaries

    Returns:
        Pandas DataFrame
    """
    return pd.DataFrame(nodes)


def edges_to_dataframe(edges):
    """
    Convert edge list to DataFrame and include a readable road label.

    Args:
        edges: List of edge dictionaries

    Returns:
        Pandas DataFrame with label column
    """
    frame = pd.DataFrame(edges)
    if not frame.empty:
        frame["label"] = frame["from_node"] + " <-> " + frame["to_node"]
    return frame


def pickups_to_dataframe(nodes):
    """
    Return pickup-group rows with the columns used in the UI.

    Args:
        nodes: List of node dictionaries

    Returns:
        Pandas DataFrame
    """
    frame = pd.DataFrame([node for node in nodes if node.get("type") == "pickup"])
    if frame.empty:
        return frame
    return frame[["id", "name", "group_size", "severity_level", "special_medical_need", "status"]]


def shelters_to_dataframe(nodes):
    """
    Return shelter/hospital rows with capacity columns for the UI.

    Args:
        nodes: List of node dictionaries

    Returns:
        Pandas DataFrame
    """
    frame = pd.DataFrame(
        [node for node in nodes if node.get("type") in {"shelter", "hospital"}]
    )
    if frame.empty:
        return frame
    return frame[["id", "name", "type", "capacity", "current_occupancy"]]
