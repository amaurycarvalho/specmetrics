# Data Model: Rule Pack Engine

## Entities

### RulePack

A self-contained collection of measurement policies loaded from a single YAML file.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Unique identifier for the Rule Pack (e.g., `"acme-corp-v1"`) |
| `description` | `str` | No | Human-readable description of the Rule Pack's purpose |
| `methodology` | `str` | No | Target measurement methodology (default: `"APF"`) |
| `rules` | `list[Rule]` | No | The set of measurement policy rules |
| `glossary_overrides` | `dict[str, str]` | No | Custom labels for function types and complexity levels |

**Validation rules**:
- `id` must be non-empty and match `^[a-zA-Z0-9_-]+$`
- If `methodology` is specified, it must be a supported methodology (`"APF"` for v1)
- At least one of `rules` or `glossary_overrides` should be present (empty Rule Packs are allowed but produce a warning)

### Rule

A single measurement policy within a Rule Pack.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Unique identifier within the Rule Pack |
| `type` | `str` | Yes | Rule type: `"exclusion"`, `"complexity_override"`, `"weight_override"`, `"vaf"`, `"element_exclusion"` |
| `description` | `str` | No | Human-readable explanation of this rule |
| `config` | `dict` | Yes | Rule-specific configuration (see rule types below) |

**Validation rules**:
- `id` must be unique within the Rule Pack
- `type` must be one of the supported rule types
- `config` content depends on `type` and must pass type-specific validation

### Rule Type: Exclusion

Excludes specific function types from counting.

```yaml
type: exclusion
config:
  function_types: ["EQ", "EO"]  # Function types to exclude
```

**Validation**: Each entry in `function_types` must be a valid `FunctionType` (`"ILF"`, `"EIF"`, `"EI"`, `"EO"`, `"EQ"`). At least one function type required.

### Rule Type: Complexity Override

Overrides the DET/RET or DET/FTR thresholds for a function type's complexity classification.

```yaml
type: complexity_override
config:
  function_type: "EI"
  thresholds:             # [Low_max, Average_max] — values beyond Average are High
    det: [4, 15]          # Low: 1-4, Average: 5-15, High: 16+
    ftr: [1, 2]           # Low: 1, Average: 2, High: 3+
```

**Validation**: `function_type` must be valid. For data functions (ILF, EIF), `ret` thresholds may be provided instead of `ftr`. Each threshold list must contain exactly 2 positive integers where the first < the second.

### Rule Type: Weight Override

Overrides the UFP weight for a specific (function_type, complexity) combination.

```yaml
type: weight_override
config:
  function_type: "EI"
  complexity: "Average"
  weight: 5
```

**Validation**: `function_type` must be valid. `complexity` must be `"Low"`, `"Average"`, or `"High"`. `weight` must be a positive integer.

### Rule Type: VAF (Value Adjustment Factor)

Defines General System Characteristics ratings for VAF computation.

```yaml
type: vaf
config:
  gsc:
    data_communications: 3
    distributed_data_processing: 2
    performance: 4
    heavily_used_configuration: 3
    transaction_rate: 3
    online_data_entry: 4
    end_user_efficiency: 3
    online_update: 3
    complex_processing: 2
    reusability: 2
    installation_ease: 2
    operational_ease: 3
    multiple_sites: 1
    facilitate_change: 2
```

**Validation**: All 14 GSC keys must be present. Each value must be an integer 0–5. The engine computes VAF = 0.65 + 0.01 * sum(GSC).

### Rule Type: Element Exclusion

Excludes specific CFM elements by ID from counting.

```yaml
type: element_exclusion
config:
  element_ids: ["fp-001", "fp-042"]
```

**Validation**: `element_ids` must be a non-empty list of strings.

### AppliedRuleRecord

An annotation on a CFM element recording which rule was applied.

| Field | Type | Description |
|-------|------|-------------|
| `rule_pack_id` | `str` | Identifier of the Rule Pack containing the rule |
| `rule_id` | `str` | Identifier of the specific rule applied |
| `rule_type` | `str` | Type of rule applied |
| `description` | `str` | Human-readable explanation of the application |
| `before_state` | `dict` | The state of the element before the rule was applied |
| `after_state` | `dict` | The state of the element after the rule was applied |

### RuleValidationReport

The output of Rule Pack validation.

| Field | Type | Description |
|-------|------|-------------|
| `loaded_files` | `list[FileLoadResult]` | Results of loading each Rule Pack file |
| `total_rules` | `int` | Total number of rules across all loaded Rule Packs |
| `active_rules` | `int` | Number of rules successfully validated and applied |
| `errors` | `list[ValidationError]` | Errors encountered during validation |
| `warnings` | `list[ValidationWarning]` | Warnings (conflicts, unused rules) |

### FileLoadResult

Result of loading a single Rule Pack file.

| Field | Type | Description |
|-------|------|-------------|
| `file_path` | `str` | Path to the loaded file |
| `rule_pack_id` | `str` | ID of the loaded Rule Pack |
| `status` | `str` | `"loaded"`, `"skipped"`, or `"error"` |
| `rules_count` | `int` | Number of rules found in the file |
| `error` | `str` | Error message if status is `"error"` |

## State Transitions

```
[Rule Pack files] → Loader → [Parsed RulePacks] → Validator → [Valid Rules]
                                                              ↓
                                              Annotator ← Applicator ← [CFM input]
                                                              ↓
                                              [Annotated CFM output]
```

1. **Loading**: Files discovered in `.specify/rules/*.yml`, parsed via ruamel.yaml into `RulePack` objects
2. **Validation**: Each RulePack and its rules validated against schema; conflicts detected across Rule Packs
3. **Application**: Valid rules applied to CFM in order: exclusions → complexity overrides → weight overrides → VAF → element exclusions
4. **Annotation**: Each applied rule recorded as an `AppliedRuleRecord` on affected CFM elements; glossary overrides applied to report labels
