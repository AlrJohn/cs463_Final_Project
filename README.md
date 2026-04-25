# Evacuation Route and Priority Planner

This project is a one-page Streamlit app for a conflict-inspired evacuation planning scenario. The app models a small road network as a weighted graph and helps a planner decide:

1. which evacuee group should be picked up next
2. which route should be taken to reach a shelter or hospital

The system balances **speed and safety** under changing road conditions.

## MVP Features

- fixed scenario based on a simplified Al-Mafraq, Jordan setting
- one vehicle, four pickup groups, two shelters, and one hospital
- user-controlled road updates: `open`, `dangerous`, `blocked`
- explicit Dijkstra-style implementation (min-heap) for weighted route computation
- greedy prioritization rule for selecting the next pickup group
- shelter and hospital capacity checks
- one-page Streamlit UI with map, controls, outputs, and ranking table

## Project Structure

```text
app.py
config.py
requirements.txt
README.md

data/
  nodes.json
  edges.json
  scenario_metadata.json

src/
  data_loader.py
  graph_builder.py
  risk_routing.py
  prioritization.py
  planner.py
  map_view.py
  state_manager.py
  utils.py
```

## How to Run

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the app:

```bash
streamlit run app.py
```

## Core Algorithm Design

### Routing
The app uses a **risk-aware Dijkstra-style algorithm** on a weighted graph.

Edge weight is computed as:

```text
(ROUTE_TRAVEL_TIME_WEIGHT * travel_time) + (ROUTE_DANGER_WEIGHT * danger_penalty)
```

- `open` roads keep their normal travel cost
- `dangerous` roads add a penalty
- `blocked` roads are removed from the working graph

Routing steps:

1. Initialize all node distances to infinity and source distance to 0.
2. Push source into a min-heap as `(distance, node)`.
3. Repeatedly pop the node with smallest distance.
4. Relax each neighbor edge using the risk-aware edge cost.
5. Reconstruct path from destination back to source using parent pointers.

Implementation details:

- `src/risk_routing.py` contains:
  - `compute_edge_cost(...)`
  - `dijkstra_path(...)` (explicit heap-based Dijkstra implementation)
  - `best_destination_path(...)`
  - `path_metrics(...)`
- `src/planner.py` runs this routing twice for each waiting group:
  - vehicle -> pickup
  - pickup -> best feasible destination
- Feasibility constraints:
  - medical-need groups can only go to hospital
  - non-medical groups are routed to shelters
  - destination must have enough remaining capacity

### Priority Selection
For each waiting pickup group, the planner evaluates:

- vehicle -> pickup path
- pickup -> best valid destination path
- severity level
- group size
- destination capacity

The current MVP score is:

```text
(severity_level * 20) + (group_size * 2) - total_route_cost
```

This keeps routing and prioritization separate:
- routing finds minimum-cost feasible paths
- scoring chooses which feasible group should be served next

Planner steps:

1. For each waiting pickup group, find vehicle -> pickup route.
2. Filter feasible destinations by medical rule and remaining capacity.
3. Find pickup -> best destination route.
4. Aggregate total cost/time/danger.
5. Score and rank all reachable groups, then choose the top option.
