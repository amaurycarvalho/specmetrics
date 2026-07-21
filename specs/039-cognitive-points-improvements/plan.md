# Implementation Plan: Cognitive Points Improvements

**Branch**: `039-cognitive-points-improvements` | **Date**: 2026-07-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/039-cognitive-points-improvements/spec.md`

## Summary

Enhance the Cognitive Points measurement engine with content-based cognitive effort estimation and sub-type Bloom classification. Each element's score becomes `bloom_weight + (content_tokens × content_multiplier)`. The Bloom classifier gains sub-type awareness (e.g., BusinessRule `derivation` → evaluate, `constraint` → apply). The default Bloom level for unknown types is changed from "analyze" (4.0) to "understand" (2.0) for more conservative scoring. Updates the payload with content token counts and documents everything in RFC-029.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: Shared `count_tokens()` from Token Points engine (spec 038), Pydantic v2 (models), structlog (logging)

**Storage**: No new storage — calibration YAML files in existing calibration directory

**Testing**: pytest

**Target Platform**: Linux (CLI)

**Project Type**: Measurement engine enhancement (follows same pattern as spec 038 Token Points improvements)

**Performance Goals**: Content tokenization adds ≤ 50ms overhead for 500 elements (reuses spec 038 tokenizer)

**Constraints**: Backward-compatible calibration YAML; shared tokenizer dependency on spec 038; no changes to CSM, CFM, or extraction pipeline

**Scale/Scope**: Single measurement engine (`cognitive_points`); 5 modified files + 1 new test file + 1 RFC update

## Constitution Check

*GATE: Must pass before Phase 0 research.*

**Engaged Principles**:
- Principle IV (LLM-Assisted, Deterministic Results): Token counting and Bloom classification are deterministic
- Principle V (Evidence First): Content token counts logged per element; Bloom classifications reference type/sub-type metadata
- Principle VI (Explainability by Design): Formula `bloom_weight + content_score` transparent and auditable
- Principle VII (Canonical Representation): Operates on CSM/CFM; no framework coupling
- Principle IX (Rule Externalization): Bloom mappings, weights, content_multiplier in external calibration
- Principle XIII (Evolution Without Disruption): Old calibration files load with new defaults; content_multiplier=0 reverts to old behavior

**Compliance Verifications**:
- [x] Deterministic Results: Same models + same calibration → same score
- [x] Evidence First: `content_token_count` field logged per CognitiveContribution
- [x] Explainability by Design: Each element's score = bloom_weight (visible) + content_score (visible)
- [x] Canonical Representation: No changes to CSM or CFM
- [x] Rule Externalization: All tuning parameters in calibration profiles
- [x] Layer Independence: Changes contained within cognitive_points engine

## Project Structure

### Documentation (this feature)

```text
specs/039-cognitive-points-improvements/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
specmetrics/
├── plugins/measurement/cognitive_points/
│   ├── bloom_classifier.py     # MODIFY: sub-type lookup, default change
│   ├── models.py               # MODIFY: content_token_count, content_score on CognitiveContribution
│   ├── calculator.py           # MODIFY: content token counting, new formula, sub-type extraction
│   ├── calibration.py          # MODIFY: content_multiplier, sub-type mappings, default change
│   └── plugin.py               # MODIFY: extended payload with content tokens
├── tests/
│   └── test_cognitive_points_content.py  # NEW: content-based + sub-type tests
├── docs/rfcs/
│   └── RFC-029 - Cognitive Points Measurement Engine.md  # MODIFY: new section
```

**Structure Decision**: No new directories. Changes tightly scoped to the cognitive_points engine. The `count_tokens()` function is imported from the Token Points engine or a shared utility (see Design Decision 1).

## Complexity Tracking

> No constitution violations.

## Design Decisions

### 1. Shared Tokenizer Location

**Decision**: Extract `count_tokens()` from `token_points/calculator.py` into `specmetrics/kernel/token_utils.py` as a shared utility. Both Token Points (spec 038) and Cognitive Points (spec 039) import from the same module.

Rationale: The function is identical in both engines. A shared location avoids code duplication and ensures consistent counting. The extraction to `kernel/` follows the Layer Independence principle — both engines depend on a stable kernel utility.

### 2. Sub-Type Attribute Extraction

**Decision**: The Bloom classifier receives the full element object (not just its type string). The classifier's `classify()` method checks the element for sub-type attributes using a configurable mapping:

```python
SUB_TYPE_ATTRS = {
    "business_rule": "rule_type",
    "operation": "operation_type",
    "specification_activity": "activity_type",
}
```

If the element's type is in `SUB_TYPE_ATTRS`, the classifier reads the corresponding attribute and constructs the lookup key `base_type.sub_type_value`. If the attribute is absent or `None`, it falls back to the base type.

### 3. Bloom Mapping Lookup Order

**Decision**: Three-tier lookup:
1. `base_type.sub_type_value` (e.g., `"business_rule.derivation"`) — if the element has a sub-type attribute
2. `base_type` (e.g., `"business_rule"`) — the existing flat mapping
3. `default_bloom_level` — now "understand" (was "analyze")

This preserves backward compatibility: elements without sub-type metadata continue to use their base type mapping.

### 4. Content Text Per Element

**Decision**: Same as Token Points — concatenate `name + " " + description` (or `name` only if no description, or `title + " " + url` for references). The function is shared via the kernel utility.

### 5. Calibration Model Updates

**Decision**: Add `content_multiplier: float = 0.1` to `CognitiveCalibrationProfile`. Update `bloom_mappings` defaults with sub-type entries. Change `default_bloom_level` from `"analyze"` to `"understand"`. Old YAML files without these fields load with the new defaults via Pydantic field defaults.
