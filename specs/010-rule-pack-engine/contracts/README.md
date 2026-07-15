# Rule Pack Engine Contracts

The Rule Pack Engine defines two contracts:

| Contract | Type | Consumers | Description |
|----------|------|-----------|-------------|
| [Pipeline Stage](#pipeline-stage-contract) | Internal (Python protocol) | Pipeline Engine, downstream stages | How the engine integrates as an EventHandler |
| [Rule Pack File Format](#rule-pack-file-format) | External (YAML schema) | Team leads, quality engineers | How organizational policies are authored |

---

## Pipeline Stage Contract

### Consumed Interfaces

The Rule Pack Engine implements the `EventHandler` protocol defined in `specmetrics.kernel.handler_registry`:

| Property/Method | Returns | Description |
|----------------|---------|-------------|
| `handled_event_type` | `EventType.RULE_PACK_APPLIED` | The event this handler subscribes to |
| `handler_id` | `str` | Unique identifier (`"rule_pack_engine"`) |
| `stage_name` | `str` | Human-readable name (`"Rule Pack Engine"`) |
| `handle(event)` | `PipelineContext` | Main execution logic |

### Event Input

```python
PipelineEvent(
    event_type=EventType.RULE_PACK_APPLIED,
    context=PipelineContext(
        canonical_model=CanonicalFunctionalModel(...),  # Input CFM
        ...
    )
)
```

### Event Output

The handler returns a modified `PipelineContext` with:
- `canonical_model` — Updated to an annotated CFM (via new `with_applied_rules(...)` method or metadata update)
- Diagnostics updated with stage timing, validation warnings, and applied rule counts

### Rules of the Contract

1. The engine MUST NOT modify the input CFM in place (it is frozen)
2. The engine MUST return a context with an annotated CFM as its sole semantic output
3. The engine MUST NOT call downstream measurement plugins directly
4. The engine MUST produce identical output for identical inputs (determinism)
5. The engine MUST NOT use LLMs or non-deterministic operations

---

## Rule Pack File Format

### File Location

- Directory: `.specify/rules/`
- Extension: `.yml` (YAML)
- Discovery: All `.yml` files in the directory, sorted alphabetically
- Load order: Files loaded in alphabetical order; for conflicting rules, the last-loaded file wins

### Schema

#### Root Structure

```yaml
# .specify/rules/acme-corp.yml
id: "acme-corp-v1"
description: "ACME Corp measurement policies for embedded systems"
methodology: "APF"           # optional, default: "APF"
glossary_overrides:          # optional
  EI: "Sensor Input"
  EO: "Control Signal"

rules:
  - id: "exclude-eq"
    type: "exclusion"
    description: "Exclude inquiries for embedded systems"
    config:
      function_types: ["EQ"]

  - id: "strict-ei-complexity"
    type: "complexity_override"
    description: "Stricter complexity thresholds for sensor inputs"
    config:
      function_type: "EI"
      thresholds:
        det: [3, 10]
        ftr: [1, 2]

  - id: "custom-ei-weights"
    type: "weight_override"
    description: "Custom weight for high-complexity sensor inputs"
    config:
      function_type: "EI"
      complexity: "High"
      weight: 6

  - id: "vaf-embedded"
    type: "vaf"
    description: "VAF for embedded systems with performance focus"
    config:
      gsc:
        data_communications: 3
        distributed_data_processing: 1
        performance: 5
        heavily_used_configuration: 4
        transaction_rate: 2
        online_data_entry: 1
        end_user_efficiency: 2
        online_update: 1
        complex_processing: 4
        reusability: 2
        installation_ease: 3
        operational_ease: 3
        multiple_sites: 1
        facilitate_change: 2
```

### Full Rule Type Reference

| Rule Type | Config Fields | Required Config |
|-----------|---------------|----------------|
| `exclusion` | `function_types: list[str]` | At least one function type |
| `complexity_override` | `function_type: str, thresholds: {det: [int, int], ?ret: [int, int], ?ftr: [int, int]}` | function_type + thresholds |
| `weight_override` | `function_type: str, complexity: str, weight: int` | All three fields |
| `vaf` | `gsc: {14 named keys: int 0-5}` | All 14 GSC keys |
| `element_exclusion` | `element_ids: list[str]` | At least one element ID |

### Validation Errors

| Error | Cause | Example |
|-------|-------|---------|
| `invalid_yaml` | File is not valid YAML | Missing colon, unclosed quote |
| `missing_id` | Rule Pack has no `id` field | — |
| `duplicate_rule_id` | Two rules in the same pack share an ID | `id: "exclude-eq"` appears twice |
| `invalid_function_type` | Rule references an unsupported function type | `"XYZ"` instead of `"ILF"`, `"EIF"`, etc. |
| `invalid_threshold` | Threshold values are not positive integers or first >= second | `det: [10, 5]` |
| `invalid_complexity` | Weight override references an unknown complexity | `"Very High"` instead of `"High"` |
| `invalid_gsc_value` | GSC value is outside 0-5 range | `7` |
| `missing_gsc_key` | VAF rule is missing one or more GSC keys | Only 12 of 14 keys provided |
