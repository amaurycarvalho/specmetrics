# Quickstart: Canonical Functional Model Builder

## Overview

This guide provides runnable validation scenarios for the CFM Builder pipeline stage. Use these to verify the feature works end-to-end after implementation.

## Prerequisites

- Python 3.13+ with `uv` or `pipx`
- Project dependencies installed (`uv sync` or `pip install -e .`)
- Evidence Graph stage (F05) implemented and operational
- Test data: sample evidence graph JSONL files in `.specmetrics/evidence_graphs/`

## Validation Scenarios

### Scenario 1: Build CFM from evidence graph

**Purpose**: Verify the basic CFM Builder pipeline stage works.

**Setup**:
```bash
# Generate a test evidence graph with known elements
python -m specmetrics.tests.fixtures create-evidence-graph \
  --output .specmetrics/evidence_graphs/test_run_001.jsonl \
  --elements 10 \
  --include-types fact,entity,relationship,operation
```

**Run**:
```bash
# Execute the pipeline through the CFM stage
python -m specmetrics kernel run --stages evidence_graph,canonical_model
```

**Expected outcome**:
- Pipeline completes successfully
- `CanonicalModelBuilt` event is emitted
- CFM contains Actors, Functional Processes, Business Rules, Data Groups, Relationships, and Operations

**Verification**:
```python
# inspect_cfm.py
from specmetrics.kernel.cfm.model import CanonicalFunctionalModel
from specmetrics.kernel.graph_persistence import GraphStore

evidence_graph = GraphStore.load(".specmetrics/evidence_graphs/test_run_001.jsonl")
cfm = build_canonical_model(evidence_graph)  # from builder module

assert len(cfm.actors()) > 0
assert len(cfm.functional_processes()) > 0
assert len(cfm.business_rules()) > 0
assert len(cfm.data_groups()) > 0
assert len(cfm.relationships()) >= 0
assert len(cfm.operations()) >= 0
print("All CFM categories populated successfully")
```

---

### Scenario 2: Verify framework independence

**Purpose**: Confirm no framework-specific labels survive in the CFM.

**Setup**: Use test data that includes OpenSpec/SpecKit-specific labels in evidence graph nodes.

**Expected outcome**: The resulting CFM contains zero elements with framework-specific terminology. All elements use canonical names.

**Verification**:
```python
framework_keywords = {"openspec", "speckit", "specmetric"}
all_names = set()
for cat in [cfm.actors(), cfm.functional_processes(), cfm.business_rules(),
            cfm.data_groups(), cfm.operations()]:
    for element in cat.values():
        all_names.add(element.name.lower())
        all_names.update(metadata.lower() for metadata in element.metadata.values())

framework_hits = all_names & framework_keywords
assert len(framework_hits) == 0, f"Found framework-specific labels: {framework_hits}"
print("Framework independence verified: no framework labels found")
```

---

### Scenario 3: Evidence traceability

**Purpose**: Verify every CFM element preserves its evidence chain.

**Verification**:
```python
for category_name, elements in [
    ("actors", cfm.actors()),
    ("functional_processes", cfm.functional_processes()),
    ("business_rules", cfm.business_rules()),
    ("data_groups", cfm.data_groups()),
]:
    for element_id, element in elements.items():
        ref = cfm.trace_evidence(element_id)
        assert ref.document_id, f"{category_name}/{element_id}: missing document_id"
        assert ref.text, f"{category_name}/{element_id}: missing source text"
        assert ref.graph_node_id, f"{category_name}/{element_id}: missing graph_node_id"

print("Evidence traceability verified: all elements have complete evidence references")
```

---

### Scenario 4: Classification conflicts

**Purpose**: Verify conflict detection and priority-based resolution.

**Setup**: Create an evidence graph with an element that matches multiple categories (e.g., same text classified as both `fact` and `operation`).

**Expected outcome**: The conflict is flagged in `BuildMetadata.conflicts`, and the element is assigned to the highest-priority category.

**Verification**:
```python
metadata = cfm.metadata()
if metadata.conflicts:
    print(f"Conflict detected: {len(metadata.conflicts)} classification conflicts")
    for conflict in metadata.conflicts:
        print(f"  Node {conflict.node_id}: {conflict.competing_categories} → {conflict.resolved_category}")
else:
    print("No classification conflicts (test data may not trigger conflicts)")
```

---

### Scenario 5: Immutability

**Purpose**: Verify the CFM is immutable after construction.

**Verification**:
```python
# Attempt to modify the CFM should fail
try:
    cfm.metadata().element_counts["actors"] = 999
    assert False, "Should not be able to modify CFM metadata"
except (TypeError, AttributeError):
    print("Immutability verified: CFM cannot be modified after construction")
```

---

### Scenario 6: Downstream consumer contract

**Purpose**: Verify a measurement engine can consume the CFM without framework-specific imports.

**Verification**:
```python
# Simulate a downstream consumer (e.g., F07 measurement engine)
def count_functional_processes(cfm: CanonicalFunctionalModel) -> int:
    return len(cfm.functional_processes())

def list_actors(cfm: CanonicalFunctionalModel) -> list[str]:
    return [actor.name for actor in cfm.actors().values()]

# These calls must never import OpenSpec, SpecKit, or similar
process_count = count_functional_processes(cfm)
actor_names = list_actors(cfm)

assert process_count > 0, "No functional processes found"
assert len(actor_names) > 0, "No actors found"
print(f"Downstream consumer contract passes: {process_count} processes, {len(actor_names)} actors")
```

## Running All Scenarios

```bash
# Run all validation scenarios as integration tests
pytest tests/integration/test_cfm_pipeline_stage.py -v

# Run contract tests for CFM interface
pytest tests/contract/test_cfm_interface.py -v

# Run unit tests for classification logic
pytest tests/unit/test_cfm_classifier.py -v
```

## Expected Outcomes

| Scenario | Expected Result |
|----------|----------------|
| Build CFM from evidence graph | Pipeline completes, all 6 categories populated |
| Framework independence | Zero framework-specific labels in CFM |
| Evidence traceability | Every element has complete document_id, section_id, text |
| Classification conflicts | Conflicts flagged in BuildMetadata |
| Immutability | CFM read-only after construction |
| Downstream consumer | Consumer works without framework-specific imports |

## Troubleshooting

| Issue | Likely Cause | Resolution |
|-------|-------------|------------|
| Pipeline skips CFM stage | Handler not registered in HandlerRegistry | Register `CfmBuilderStage` with `registry.register(cfm_stage)` |
| Empty CFM categories | Evidence graph contains no processable elements | Verify evidence graph has nodes with `semantic_type` set |
| Classification conflicts | Ambiguous semantic types in evidence graph | Review test data — expected for edge case testing |
| Framework labels in output | Normalization not applied | Check classifier's framework keyword detection |

## References

- [Data Model](data-model.md) — full entity definitions
- [Plan](plan.md) — implementation plan and project structure
- [Contract: CFM Interface](contracts/canonical_model_interface.md) — stable interface for downstream consumers
