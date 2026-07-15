# Contract: CanonicalFunctionalModel Interface

## Purpose

This contract defines the public interface of the `CanonicalFunctionalModel` — the sole contract that downstream measurement engine plugins (F07), rule engines (F09), and other consumers depend on. This interface is framework-agnostic and stable across pipeline runs.

**Important**: Consumers MUST NOT depend on internal implementation details (classifier logic, builder internals, serialization format). Only this documented interface is stable.

## Interface Methods

### Enumeration

```python
def actors() -> dict[str, Actor]
```
Returns all Actors in the model indexed by ID. Empty dict if none.

```python
def functional_processes() -> dict[str, FunctionalProcess]
```
Returns all FunctionalProcesses indexed by ID. Empty dict if none.

```python
def business_rules() -> dict[str, BusinessRule]
```
Returns all BusinessRules indexed by ID. Empty dict if none.

```python
def data_groups() -> dict[str, DataGroup]
```
Returns all DataGroups indexed by ID. Empty dict if none.

```python
def relationships() -> list[Relationship]
```
Returns all Relationships as an ordered list. Empty list if none.

```python
def operations() -> dict[str, Operation]
```
Returns all Operations indexed by ID. Empty dict if none.

### Query

```python
def get_element(element_id: str) -> Actor | FunctionalProcess | BusinessRule | DataGroup | Relationship | Operation | UnclassifiedElement | None
```
Returns any CFM element by its unique ID, or `None` if not found.

```python
def get_elements_by_evidence(document_id: str) -> list[Any]
```
Returns all CFM elements that trace back to a given document, using their evidence references.

```python
def get_elements_by_category(category: str) -> dict[str, Any]
```
Returns all elements of a specific category by name (`"actors"`, `"functional_processes"`, `"business_rules"`, `"data_groups"`, `"relationships"`, `"operations"`, `"unclassified"`).

### Traversal

```python
def get_relationships_for_element(element_id: str) -> list[Relationship]
```
Returns all relationships where the given element is either source or target.

```python
def trace_evidence(element_id: str) -> EvidenceRef
```
Returns the evidence reference chain for a given element, tracing back through the evidence graph to the original specification text.

### Metadata

```python
def run_id() -> str
```
Returns the pipeline run identifier.

```python
def metadata() -> BuildMetadata
```
Returns build metadata including element counts, conflicts, and duration.

```python
def evidence_graph_ref() -> str
```
Returns the source EvidenceGraph run_id for provenance tracing.

## Serialization

```python
def model_dump() -> dict
```
Returns the complete CFM as a JSON-serializable dictionary conforming to Pydantic v2's `model_dump()` semantics.

```python
@classmethod
def model_validate(data: dict) -> CanonicalFunctionalModel
```
Constructs a CFM from a dictionary (for deserialization or testing). Validates all constraints on construction.

## Usage Example (Downstream Consumer)

```python
# A measurement engine consuming the CFM:
cfm: CanonicalFunctionalModel = event.context.canonical_model

for process_id, process in cfm.functional_processes().items():
    actor_names = [cfm.get_element(aid).name for aid in process.actor_ids]
    operation_count = len(process.operation_ids)
    data_groups = [cfm.get_element(did).name for did in process.data_group_ids]

    # ... perform measurement logic using only CFM data ...
```

## Stability Guarantee

| Element | Stability |
|---------|-----------|
| Enumeration methods (actors(), functional_processes(), etc.) | Stable — will not be removed |
| get_element() | Stable — will not be removed |
| metadata() | Stable — will not be removed |
| model_dump() / model_validate() | Stable — will not be removed |
| New query methods | Additive only — never break existing consumers |
| Internal classifications or entity IDs | May change between runs — consumers must not rely on specific ID formats |

## Contract Testing

Downstream consumers MUST verify:
1. All six element categories are accessible through documented enumeration methods
2. Evidence references are preserved and traceable for every element
3. No framework-specific labels appear in any element's name, description, or metadata
4. The model is immutable — calling methods does not modify internal state
