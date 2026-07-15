# Quickstart: Semantic Extraction

## Prerequisites

- Python 3.13+
- Dependencies installed (`pytest`, `litellm`)
- F01 (Kernel & Pipeline Engine) implemented and tested
- F02 (Plugin Discovery & Registry) implemented and tested
- F03 (Specification Adapter Interface) implemented and tested
- Test virtualenv activated

## Setup

```bash
source .venv/bin/activate
```

## Validation Scenarios

### Scenario 1: Extraction Provider Interface Compliance

```bash
pytest tests/unit/test_extraction_provider.py -v
```

**Expected outcome**: All tests pass. Verifies that:
- The `ExtractionProvider` Protocol requires `extract()` and `supports_type()` methods
- `ExtractionResult` and `ExtractedElement` models accept valid fields
- Evidence provenance is correctly tracked

### Scenario 2: Extraction Stage Integration

```bash
pytest tests/unit/test_extraction_stage.py -v
```

**Expected outcome**: All tests pass. Verifies that:
- `ExtractionStage` registers as an `EventHandler` for `DOCUMENTS_DISCOVERED`
- Stage routes documents to the correct provider based on type
- Per-document error isolation works (one failing document does not block others)
- Empty extraction results are handled gracefully

### Scenario 3: Pipeline Integration

```bash
pytest tests/integration/test_extraction_pipeline.py -v
```

**Expected outcome**: All tests pass. Verifies that:
- A mock extraction provider registered via F02 is invoked during pipeline execution
- Extracted elements are included in the `SEMANTIC_EXTRACTION_COMPLETED` event payload
- The extraction result is consumable by downstream stages

### Scenario 4: All Tests

```bash
pytest tests/
```

**Expected outcome**: All previous F01, F02, and F03 tests pass — no regressions.

## Contracts Reference

- [Extraction Interface Contract](contracts/extraction-interface.md) — How extraction providers must be structured and registered

## Data Model Reference

- [Data Model](data-model.md) — ExtractedElement, EvidenceReference, ExtractionResult, and ExtractionProvider definitions
