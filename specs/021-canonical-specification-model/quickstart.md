# Quickstart: Canonical Specification Model Builder

## Prerequisites

- Python >= 3.12 with `uv` or `pipx`
- Clone of `specmetrics` at branch `021-canonical-specification-model`
- Dependencies installed: `uv sync` (or `pip install -e ".[dev]"`)

## Setup

```bash
# From repo root
uv sync
```

## Validation Scenarios

### Scenario 1: Build CSM from a known evidence graph

```bash
# Use the test helper to create a sample evidence graph with specification artifacts
# and run the CSM builder stage
python -m pytest tests/unit/test_csm_builder.py -v -k test_build_from_openspec_graph
```

**Expected**: CSM contains decisions, assumptions, open questions, acceptance criteria, glossary terms, constraints, risks, specification activities. Zero framework-specific terminology. All elements have UUIDs and evidence references.

**Data model reference**: `specs/021-canonical-specification-model/data-model.md`
**Contract reference**: `specs/021-canonical-specification-model/contracts/csm-consumer-protocol.md`

### Scenario 2: Test normalization across frameworks

```bash
python -m pytest tests/unit/test_csm_builder.py -v -k test_framework_normalization
```

**Expected**: Evidence graphs from OpenSpec and SpecKit produce CSMs with identical structures (same categories, same entity types) differing only in evidence content.

### Scenario 3: Empty evidence graph

```bash
python -m pytest tests/unit/test_csm_builder.py -v -k test_empty_graph
```

**Expected**: Builder produces an empty CSM (all category dictionaries empty). Completes successfully without errors. BuildMetadata shows zero counts.

### Scenario 4: Unclassifiable elements preserved

```bash
python -m pytest tests/unit/test_csm_builder.py -v -k test_unclassifiable_elements
```

**Expected**: Elements that cannot be classified appear in the `references` category with their original text preserved.

### Scenario 5: Performance benchmark

```bash
python -m pytest tests/unit/test_csm_builder.py -v -k test_performance_500_elements --benchmark-only
```

**Expected**: 500 elements processed in under 3 seconds (SC-001). Benchmark recorded for regression tracking.

### Scenario 6: Downstream consumer contract

```bash
python -m pytest tests/contract/test_csm_interface.py -v
```

**Expected**: A mock measurement engine consuming only the CSM interface (via `CsmConsumer` protocol) successfully enumerates categories and queries elements without any framework-specific imports.

### Scenario 7: Full pipeline integration

```bash
python -m pytest tests/integration/test_csm_pipeline_stage.py -v
```

**Expected**: The pipeline executes Evidence Graph → CSM Builder stages. The `CanonicalSpecificationModelBuilt` event is emitted. `PipelineContext.canonical_spec_model` contains the built CSM.

## Key Contracts

| Artifact | Path |
|----------|------|
| Data model | `specs/021-canonical-specification-model/data-model.md` |
| Consumer protocol | `specs/021-canonical-specification-model/contracts/csm-consumer-protocol.md` |
| Event contract | `specs/021-canonical-specification-model/contracts/event-contract.md` |
| Spec | `specs/021-canonical-specification-model/spec.md` |
