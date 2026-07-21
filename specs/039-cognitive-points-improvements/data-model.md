# Data Model: Cognitive Points Improvements

**Feature**: 039-cognitive-points-improvements

## Overview

Three existing models are updated, one shared utility is referenced. The scoring formula changes from `score = bloom_weight` to `score = bloom_weight + (content_tokens × content_multiplier)`. The Bloom classifier gains a three-tier lookup: sub-type → base type → default.

---

## CognitiveContribution (Updated)

**File**: `specmetrics/plugins/measurement/cognitive_points/models.py`

| Field | Type | Change | Description |
|-------|------|--------|-------------|
| `element_id` | `str` | Unchanged | Unique element identifier |
| `element_type` | `str` | Unchanged | Collection name or base type |
| `element_name` | `str` | Unchanged | Human-readable name (truncation removed or increased) |
| `model_source` | `str` | Unchanged | "csm" or "cfm" |
| `bloom_level` | `str` | Unchanged | Bloom taxonomy level name |
| `cognitive_weight` | `float` | Unchanged | Bloom level weight (1.0–8.0) |
| `content_token_count` | `int` | **NEW** | Tokens in element's text content |
| `content_score` | `float` | **NEW** | `content_token_count × content_multiplier` |
| `partial_score` | `float` | **Changed semantics** | Now equals `cognitive_weight + content_score` (was just `cognitive_weight`) |

**Validation**: `partial_score` MUST equal `cognitive_weight + content_score` (within 0.001 tolerance).

---

## Bloom Classifier (Updated)

**File**: `specmetrics/plugins/measurement/cognitive_points/bloom_classifier.py`

**Method signature change**:
```python
# Old:
def classify(self, element_type: str) -> str

# New:
def classify(self, element_type: str, element: Any = None) -> str
```

**Lookup order** (when `element` is provided):
1. `base_type.sub_type_value` — if element has a sub-type attribute and the value is known
2. `base_type` — the existing flat mapping
3. `default_bloom_level` — "understand" (was "analyze")

**Sub-type attribute mapping** (internal to classifier):
```python
SUB_TYPE_ATTRS = {
    "business_rule": "rule_type",
    "operation": "operation_type",
    "specification_activity": "activity_type",
}
```

---

## Updated Bloom Mappings (Default)

**File**: `specmetrics/plugins/measurement/cognitive_points/bloom_classifier.py` and `calibration.py`

### Base type mappings (unchanged from current):

| Element Type | Bloom Level | Weight |
|---|---|---|
| exploration | understand | 2.0 |
| clarification | analyze | 4.0 |
| refinement | apply | 3.0 |
| review | evaluate | 5.0 |
| validation | evaluate | 5.0 |
| decision | evaluate | 5.0 |
| assumption | understand | 2.0 |
| constraint | apply | 3.0 |
| risk | analyze | 4.0 |
| open_question | analyze | 4.0 |
| acceptance_criterion | apply | 3.0 |
| glossary_term | remember | 1.0 |
| functional_process | create | 8.0 |
| business_rule | apply | 3.0 |
| operation | apply | 3.0 |
| data_group | understand | 2.0 |
| relationship | understand | 2.0 |
| actor | remember | 1.0 |

### Sub-type mappings (NEW):

| Key | Bloom Level | Weight |
|---|---|---|
| `business_rule.constraint` | apply | 3.0 |
| `business_rule.condition` | analyze | 4.0 |
| `business_rule.policy` | evaluate | 5.0 |
| `business_rule.derivation` | evaluate | 5.0 |
| `operation.standard` | apply | 3.0 |
| `operation.conditional` | analyze | 4.0 |
| `operation.iterative` | analyze | 4.0 |
| `operation.transactional` | create | 8.0 |

---

## CognitiveCalibrationProfile (Updated)

**File**: `specmetrics/plugins/measurement/cognitive_points/calibration.py`

| Field | Type | Old Default | New Default |
|-------|------|-------------|-------------|
| `version` | `str` | "1.0" | Unchanged |
| `name` | `str \| None` | None | Unchanged |
| `bloom_levels` | `dict[str, float]` | 6 levels (1.0–8.0) | Unchanged |
| `bloom_mappings` | `dict[str, str]` | 18 base types | 18 base types + 8 sub-type keys |
| `default_bloom_level` | `str` | "analyze" | **"understand"** |
| `fibonacci_normalization` | `FibonacciNormalizationConfig` | 7 thresholds | Unchanged |
| `content_multiplier` | `float` | (did not exist) | **0.1** (NEW) |

**Validation**: `content_multiplier` >= 0.0. Set to 0.0 to disable content-based scoring and revert to pure Bloom taxonomy scoring.

---

## Payload Extensions (plugin.py)

| Key | Type | Description |
|-----|------|-------------|
| `cognitive_content_multiplier` | `float` | The content_multiplier used |
| `cognitive_content_tokens` | `dict[str, int]` | Total content tokens per element type |

Each entry in `cognitive_element_counts` gains:

| Field | Type | Change |
|-------|------|--------|
| `count` | `int` | Unchanged |
| `total` | `float` | Unchanged (sum of partial_scores) |
| `content_tokens` | `int` | **NEW** (sum of content_token_count for elements of this type) |

---

## Updated Calculation Flow

```
for each CSM/CFM element:
    base_type = collection_name.rstrip("s") or activity.activity_type
    sub_type = element.{SUB_TYPE_ATTRS[base_type]} if base_type in SUB_TYPE_ATTRS else None

    bloom_level = classifier.classify(base_type, element)
    bloom_weight = calibration.bloom_levels[bloom_level]

    content_text = element.name + " " + element.description (or name only)
    content_tokens = count_tokens(content_text)  # from kernel/token_utils.py
    content_score = content_tokens × content_multiplier

    partial_score = bloom_weight + content_score
```

---

## Shared Tokenizer Dependency

**File**: `specmetrics/kernel/token_utils.py` (created by spec 038, shared by spec 039)

```python
def count_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except ImportError:
        return max(1, len(text) // 4)
```
