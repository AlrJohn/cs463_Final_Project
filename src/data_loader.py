"""Utilities for loading scenario data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"


def _read_json(path: Path) -> list[dict[str, Any]] | dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_nodes() -> list[dict[str, Any]]:
    return list(_read_json(DATA_DIR / "nodes.json"))


def load_edges() -> list[dict[str, Any]]:
    return list(_read_json(DATA_DIR / "edges.json"))


def load_metadata() -> dict[str, Any]:
    metadata = _read_json(DATA_DIR / "scenario_metadata.json")
    if not isinstance(metadata, dict):
        raise ValueError("Scenario metadata must be a JSON object.")
    return metadata


def nodes_to_dataframe(nodes: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(nodes)


def edges_to_dataframe(edges: list[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(edges)
    if not frame.empty:
        frame["label"] = frame["from_node"] + " <-> " + frame["to_node"]
    return frame


def pickups_to_dataframe(nodes: list[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame([node for node in nodes if node.get("type") == "pickup"])
    if frame.empty:
        return frame
    return frame[[
        "id",
        "name",
        "group_size",
        "severity_level",
        "special_medical_need",
        "status",
    ]]


def shelters_to_dataframe(nodes: list[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(
        [node for node in nodes if node.get("type") in {"shelter", "hospital"}]
    )
    if frame.empty:
        return frame
    return frame[["id", "name", "type", "capacity", "current_occupancy"]]
