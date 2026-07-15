# Quickstart: APF Measurement Plugin

## Prerequisites

- SpecMetrics Kernel (F01) with Pipeline Engine and Plugin Registry
- Canonical Functional Model output from F06
- Python 3.13 with `pytest` installed
- (Optional) Rule Pack YAML file for organizational customizations

## Setup

The APF measurement plugin is discovered automatically via Python Entry Points when installed:

```bash
# From the specmetrics repository root
pip install -e .

# Verify plugin discovery
specmetrics plugins list
# Expected output includes: "apf — IFPUG/APF Function Point Analysis (measurement)"
```

## Validation Scenarios

### Scenario 1: Basic APF Measurement

**Purpose**: Verify that a valid CFM produces correct function point counts.

**Setup**:

```bash
# Create a test CFM fixture (or use the built-in test helper)
# See: specs/008-measurement-engine-apf/tests/unit/test_counter.py
```

**Command**:

```python
# From Python REPL or test
from specmetrics.plugins.measurement.apf import APFMeasurementPlugin
from specmetrics.kernel.canonical_model import CanonicalFunctionalModel

plugin = APFMeasurementPlugin()
cfm = load_test_cfm()  # CFM with known DataGroups and Operations
result = plugin.measure(cfm)

print(result.summary.total_ufp)       # Expected: known UFP value
print(result.summary.total_function_count)  # Expected: matching count
```

**Expected Outcome**:
- `result.summary.total_function_count` matches the number of identifiable functions in the CFM
- Each `MeasuredFunction` has a valid `function_type`, `complexity`, and `ufp_weight`
- No warnings or errors in the result

**Contract Reference**: [measurement-plugin-interface.md](contracts/measurement-plugin-interface.md) — `MeasurementPlugin.measure()` method

---

### Scenario 2: Explainability — Evidence Trail

**Purpose**: Verify every measured function preserves traceability to source evidence.

**Setup**: Same as Scenario 1.

**Command**:

```python
result = plugin.measure(cfm)
for fn in result.measured_functions:
    assert len(fn.evidence_refs) > 0, f"Function {fn.id} has no evidence trail"
    for ref in fn.evidence_refs:
        assert ref.graph_node_id, f"EvidenceRef missing graph_node_id"
        assert ref.text, f"EvidenceRef missing source text"

# Request full explanation
for explanation in result.explanations:
    print(f"{explanation.function_id}: {explanation.classification_reason}")
    print(f"  Complexity: {explanation.complexity_reason}")
```

**Expected Outcome**:
- 100% of measured functions have non-empty evidence trails
- Each explanation includes `classification_reason`, `complexity_reason`, and `evidence_chain`
- Functions with Rule Pack exceptions include `rule_exceptions` details

**Spec Reference**: [spec.md](../spec.md) — FR-007, User Story 2

---

### Scenario 3: Rule Pack Customization

**Purpose**: Verify that Rule Packs correctly modify measurement behavior.

**Setup**: Create a Rule Pack YAML that excludes External Inquiries:

```yaml
# test_rule_pack.yml
rule_pack:
  id: "test-no-eq"
  methodology: "APF"
  excluded_types: ["EQ"]
```

**Command**:

```python
from specmetrics.kernel.rule_pack import RulePack

rule_pack = RulePack.from_yaml("test_rule_pack.yml")

# Measure without Rule Pack
result_default = plugin.measure(cfm)

# Measure with Rule Pack
result_custom = plugin.measure(cfm, rule_pack)

eq_in_default = [f for f in result_default.measured_functions 
                 if f.function_type == "EQ"]
eq_in_custom = [f for f in result_custom.measured_functions 
                if f.function_type == "EQ"]

print(f"EQ count (default): {len(eq_in_default)}")
print(f"EQ count (custom): {len(eq_in_custom)}")
```

**Expected Outcome**:
- `len(eq_in_custom) == 0`
- `result_custom.summary.total_ufp` == `result_default.summary.total_ufp - sum(eq_in_default.ufp_weight)`
- The CFM is not modified — only the measurement output changes

**Data Model Reference**: [data-model.md](../data-model.md) — `APFMeasurementResult`, `MeasuredFunction`
**Contract Reference**: [measurement-plugin-interface.md](contracts/measurement-plugin-interface.md) — Rule Pack contract

---

### Scenario 4: Plugin Discovery

**Purpose**: Verify the APF plugin is discoverable via Python Entry Points.

**Setup**: Ensure the plugin package is installed.

**Command**:

```bash
python -c "
from importlib.metadata import entry_points
eps = entry_points(group='specmetrics.plugins.measurement')
for ep in eps:
    print(f'Discovered: {ep.name} -> {ep.value}')
"
```

**Expected Outcome**:
- Output includes: `Discovered: apf -> specmetrics.plugins.measurement.apf:APFMeasurementPlugin`

**Spec Reference**: [spec.md](../spec.md) — FR-009, User Story 4

---

### Scenario 5: Determinism Verification

**Purpose**: Verify that identical inputs produce byte-identical results.

**Command**:

```python
result_a = plugin.measure(cfm)
result_b = plugin.measure(cfm)

from pydantic import BaseModel
json_a = result_a.model_dump_json()
json_b = result_b.model_dump_json()

assert json_a == json_b, "Determinism violation: identical inputs differ"
print("Determinism verified: outputs are byte-identical")
```

**Expected Outcome**: `json_a == json_b` — no assertion error.

**Spec Reference**: [spec.md](../spec.md) — FR-006, SC-004

## Running the Full Validation Suite

```bash
cd /path/to/specmetrics
pytest tests/unit/measurement/apf/ -v
pytest tests/integration/measurement/apf/ -v
```

**Expected**: All tests pass. Contract tests verify the plugin satisfies the `MeasurementPlugin` protocol.
