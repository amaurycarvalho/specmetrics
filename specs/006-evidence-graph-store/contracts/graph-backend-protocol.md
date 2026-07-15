# Contract: Graph Backend Protocol

**Version**: 1.0.0 | **Date**: 2026-07-15 | **Spec**: [spec.md](../spec.md) | **Data Model**: [data-model.md](../data-model.md)

---

## Purpose

Defines the interface that every graph backend must implement. Backends provide the underlying graph data structure and traversal operations. The reference implementation uses NetworkX; alternative backends (iGraph, SQL, Neo4j) can be swapped in by implementing this Protocol.

---

## Interface

### `add_node(node_id: str, attrs: dict) -> None`

Add a node with the given identifier and attributes.

**Rules**:
- MUST NOT overwrite an existing node with the same `node_id` — raise `NodeAlreadyExistsError` instead
- MUST accept any `attrs` dictionary; validation of required fields is the caller's responsibility
- MUST be O(1) amortized

### `add_edge(source: str, target: str, attrs: dict) -> None`

Add a directed edge from `source` to `target`.

**Rules**:
- MUST raise `NodeNotFoundError` if either `source` or `target` does not exist
- MUST NOT overwrite an existing edge between the same pair — append as multi-edge or raise `EdgeAlreadyExistsError`
- Self-loops (source == target) MUST raise `SelfLoopError`

### `get_node(node_id: str) -> dict | None`

Retrieve a node's attributes by ID.

**Rules**:
- MUST return `None` (not raise) for non-existent `node_id`
- MUST return a copy of the attributes to prevent caller mutations

### `query_nodes(filters: dict) -> list[dict]`

Query nodes matching the given filter criteria.

**Supported filters**:
- `node_type` — exact match on `Literal["extracted_element", "evidence"]`
- `semantic_type` — exact match on `Literal["fact", "entity", "relationship", "operation"]`
- `document_id` — exact match on string
- Combination filters use AND semantics (all must match)

**Rules**:
- MUST return an empty list (not raise) when no nodes match
- Unrecognized filter keys MUST be ignored (not raise)
- MUST complete in O(n) or better where n is the node count

### `traverse(start_id: str, direction: Literal["forward", "reverse"], max_depth: int) -> list[list[dict]]`

Traverse the graph from the given start node.

**Rules**:
- `direction="forward"` follows edges from source → target
- `direction="reverse"` follows edges from target → source (for provenance queries)
- Returns a list of paths, where each path is a list of node attribute dicts
- `max_depth=0` returns only the start node
- MUST raise `NodeNotFoundError` if `start_id` does not exist
- Cyclic graphs MUST be handled without infinite loops (track visited nodes)

### `to_serializable() -> dict`

Serialize the graph to a JSON-compatible dictionary.

**Rules**:
- MUST return a dict with keys `"nodes"` and `"edges"`
- Nodes value is a list of dicts, each with at minimum `"id"` key
- Edges value is a list of dicts, each with `"source"`, `"target"`, and `"edge_type"` keys
- Deterministic — same graph always produces the same serializable output (stable order)

### `from_serializable(data: dict) -> None`

Deserialize a JSON-compatible dictionary to populate the graph.

**Rules**:
- MUST clear any existing nodes/edges before loading
- MUST validate that all edge references resolve to existing nodes and raise `InvalidGraphDataError` otherwise
- MUST accept the same format produced by `to_serializable()`

---

## Exception Types

| Exception | Raised When |
|-----------|-------------|
| `NodeNotFoundError` | Referenced node ID does not exist |
| `NodeAlreadyExistsError` | `add_node` called with an existing node ID |
| `EdgeAlreadyExistsError` | `add_edge` called with an already-existing edge |
| `SelfLoopError` | `add_edge` called with identical source and target |
| `InvalidGraphDataError` | `from_serializable` receives invalid or corrupted data |

---

## Example: NetworkX Backend

```python
import networkx as nx
from typing import Any

class NetworkXBackend:
    def __init__(self):
        self._graph = nx.DiGraph()

    def add_node(self, node_id: str, attrs: dict) -> None:
        if self._graph.has_node(node_id):
            raise NodeAlreadyExistsError(node_id)
        self._graph.add_node(node_id, **attrs)

    def add_edge(self, source: str, target: str, attrs: dict) -> None:
        if not self._graph.has_node(source):
            raise NodeNotFoundError(source)
        if not self._graph.has_node(target):
            raise NodeNotFoundError(target)
        if source == target:
            raise SelfLoopError(source)
        self._graph.add_edge(source, target, **attrs)

    def get_node(self, node_id: str) -> dict | None:
        if not self._graph.has_node(node_id):
            return None
        return dict(self._graph.nodes[node_id])

    def query_nodes(self, filters: dict) -> list[dict]:
        results = []
        for node_id, data in self._graph.nodes(data=True):
            matches = all(
                data.get(k) == v for k, v in filters.items()
                if k in data
            )
            if matches:
                entry = {"id": node_id, **data}
                results.append(entry)
        return results

    def traverse(self, start_id: str, direction: str, max_depth: int) -> list[list[dict]]:
        if not self._graph.has_node(start_id):
            raise NodeNotFoundError(start_id)
        nodes = {start_id}
        paths = [[{"id": start_id, **dict(self._graph.nodes[start_id])}]]
        for _ in range(max_depth):
            new_paths = []
            for path in paths:
                last_id = path[-1]["id"]
                neighbors = (
                    self._graph.successors(last_id)
                    if direction == "forward"
                    else self._graph.predecessors(last_id)
                )
                for neighbor in neighbors:
                    if neighbor not in {n["id"] for n in path}:
                        new_paths.append(path + [{"id": neighbor, **dict(self._graph.nodes[neighbor])}])
            paths = new_paths
            if not paths:
                break
        return paths

    def to_serializable(self) -> dict:
        return nx.node_link_data(self._graph)

    def from_serializable(self, data: dict) -> None:
        self._graph = nx.node_link_graph(data)
```

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| `add_node` with existing ID | Raise `NodeAlreadyExistsError` |
| `add_edge` with non-existent source | Raise `NodeNotFoundError` |
| `traverse` with non-existent start | Raise `NodeNotFoundError` |
| `from_serializable` with missing edge targets | Raise `InvalidGraphDataError` |
| Unrecognized filter key in `query_nodes` | Silently ignored |
| `get_node` with non-existent ID | Return `None` |
