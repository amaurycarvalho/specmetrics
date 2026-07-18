# Quickstart: Specialized Deterministic Fallbacks

## Prerequisites

- Python 3.13+ with `uv` or `pipx`
- specmetrics installed from source (`pip install -e .`)
- Access to a SpecKit repository (e.g., specmetrics itself) and/or OpenSpec examples in `tests/openspec/`

## Setup

```bash
# Install specmetrics from source
cd /path/to/specmetrics
pip install -e .

# Verify rule packs exist
ls specmetrics/kernel/rules/speckit_rules.yaml
ls specmetrics/kernel/rules/openspec_rules.yaml
```

## Validation Scenarios

### Scenario 1: Speckit extraction on specmetrics itself

```bash
# Run deterministic extraction on specmetrics' own specs
specmetrics measure --engine deterministic --repo ./specs/
```

**Expected outcome**: The pipeline completes successfully. CFM contains non-empty actors, functional_processes, business_rules, data_groups. CSM contains non-empty decisions, assumptions, constraints, acceptance_criteria. Total extraction time for 29 features should be within acceptable limits.

### Scenario 2: OpenSpec extraction on tests/openspec/

```bash
# Run deterministic extraction on tests/openspec/
specmetrics measure --engine deterministic --repo tests/openspec/
```

**Expected outcome**: The pipeline completes ≤ 30s. CFM contains at least 15 elements across actors, business_rules, data_groups, operations. CSM contains at least 8 elements across decisions, risks, assumptions, specification_activities. All extraction is deterministic — no LLM API calls made.

### Scenario 3: Verify all 8 measurement plugins produce non-zero results

```bash
# Run all measurement plugins
specmetrics measure --engine deterministic --repo ./specs/ --all-plugins
```

**Expected outcome**: FPA, SFP, SNAP, Token Points, Cognitive Points, Story Points, T-Shirt, and BCP plugins all produce non-zero outputs from deterministic-only extraction.

### Scenario 4: Verify byte-identical re-execution

```bash
# Run twice and compare
specmetrics measure --engine deterministic --repo ./specs/ --output /tmp/run1.json
specmetrics measure --engine deterministic --repo ./specs/ --output /tmp/run2.json
diff <(jq 'del(.duration_ms)' /tmp/run1.json) <(jq 'del(.duration_ms)' /tmp/run2.json)
```

**Expected outcome**: No differences except `duration_ms`.

## Data Model Reference

See [data-model.md](data-model.md) for entity definitions and field types.

## Contract Reference

See [contracts/rule-pack-contract.md](contracts/rule-pack-contract.md) for the rule pack YAML schema and extraction contract rules.

## Key Metrics

| Metric | Target |
|--------|--------|
| `tests/openspec/` end-to-end time | ≤ 30s |
| Per-document extraction success rate | ≥ 99% |
| SpecKit elements extracted (from 007-canonical-functional-model/spec.md) | ≥ 20 |
| OpenSpec master spec elements (from tests/openspec/specs/ticker-analysis/spec.md) | ≥ 25 |
| OpenSpec design.md decisions extracted (from tests/openspec/changes/) | ≥ 18 |
| OpenSpec total elements across all 29 specs | ≥ 60 |
