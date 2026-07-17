# Quickstart: Semantic Extraction Engine

## Prerequisites

- Python 3.13+
- Dependencies installed (`pytest`, `structlog`, `pydantic`, `markdown-it-py`, `litellm`)
- F01 (Kernel & Pipeline Engine) implemented and tested
- F03 (Specification Adapter Interface) implemented and tested
- F04/F05 (existing extraction provider infrastructure) implemented and tested
- Test virtualenv activated

## Setup

```bash
source .venv/bin/activate
```

## Validation Scenarios

### Scenario 1: Engine Interface Compliance

```bash
pytest tests/unit/test_semantic_extraction_engine.py -v
```

**Expected outcome**: All tests pass. Verifies that:
- `SemanticExtractionEngine` Protocol requires `extract()` method
- `ExtractionResult`, `ExtractedElement`, `EvidenceReference` models accept valid fields
- `SemanticEngineFactory.create()` resolves all five provider strings correctly
- Factory raises `ValueError` for unknown provider strings

### Scenario 2: Deterministic Engine Extraction

```bash
pytest tests/unit/test_deterministic_engine.py -v
```

**Expected outcome**: All tests pass. Verifies that:
- `DeterministicSemanticEngine` processes documents with headings, lists, tables, code blocks, blockquotes, emphasis, and links
- Output contains semantic elements for each recognized structural pattern (FR-007)
- Same document processed twice produces byte-identical output (NFR-001)
- Rule packs are loaded and rules are matched by priority (Q3)
- Evidence references have non-empty `document_id` and `text` on every element (FR-010)
- Content-hash IDs are deterministic and unique per element (Q2)
- Statistics are reported in `ProcessingStats` (Q5)

### Scenario 3: LiteLLM Engine Extraction

```bash
pytest tests/unit/test_litellm_engine.py -v
```

**Expected outcome**: All tests pass. Verifies that:
- `LiteLLMSemanticEngine` produces `ExtractionResult` matching the same data model as deterministic engine (FR-009)
- Confidence scores are included (Q4)
- Provider failure raises structured error — no silent fallback to deterministic (FR-012, Q1)
- Evidence references are preserved (FR-010)

### Scenario 4: Pipeline Integration

```bash
pytest tests/integration/test_engine_pipeline.py -v
```

**Expected outcome**: All tests pass. Verifies that:
- Pipeline initializes `SemanticEngineFactory` once (NFR-002)
- Pipeline invokes only `SemanticExtractionEngine` interface (FR-005)
- Switching provider requires no pipeline reconfiguration (SC-003)
- Downstream stages receive identical `ExtractionResult` format regardless of engine (NFR-003)

### Scenario 5: All Tests

```bash
pytest tests/
```

**Expected outcome**: All existing F01–F05 tests pass — no regressions.

## Contracts Reference

- [Engine Interface Contract](contracts/engine-interface.md) — How the engine interface and factory must be structured

## Data Model Reference

- [Data Model](data-model.md) — SemanticExtractionEngine, ExtractionResult, ExtractedElement, EvidenceReference, ProcessingStats, ExtractionRule definitions
