# Evacuation Route and Priority Planner

This project is a one-page Streamlit app for a conflict-inspired evacuation planning scenario. The app models a small road network as a weighted graph and helps a planner decide:

1. which evacuee group should be picked up next
2. which route should be taken to reach a shelter or hospital

The system balances **speed and safety** under changing road conditions.

## MVP Features

- fixed scenario based on a simplified Al-Mafraq, Jordan setting
- one vehicle, four pickup groups, two shelters, and one hospital
- user-controlled road updates: `open`, `dangerous`, `blocked`
- Dijkstra's algorithm for weighted route computation
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
  routing.py
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
The app uses **Dijkstra's algorithm** on a weighted graph.

Edge weight is computed as:

```text
travel_time + danger_penalty
```

- `open` roads keep their normal travel cost
- `dangerous` roads add a penalty
- `blocked` roads are removed from the working graph

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

## Suggested Next Steps

- add alternate route suggestions
- compare before/after route states
- allow optional hospital-only routing for severe groups
- export a short scenario summary for the final presentation
