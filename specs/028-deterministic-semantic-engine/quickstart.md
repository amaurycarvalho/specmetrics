# Quickstart: Deterministic Semantic Engine

## Prerequisites

- Python 3.13+
- Dependencies installed (`pytest`, `structlog`, `pydantic`, `markdown-it-py`, `ruamel.yaml`)
- F01 (Kernel & Pipeline Engine) implemented and tested
- F03 (Specification Adapter Interface) implemented and tested
- F27 (Semantic Extraction Engine interface + factory) implemented and tested
- Test virtualenv activated

## Setup

```bash
source .venv/bin/activate
```

## Validation Scenarios

### Scenario 1: AST Visitor Compliance

```bash
pytest tests/unit/test_engine_visitors.py -v
```

**Expected outcome**: All tests pass. Verifies that:
- HeadingVisitor collects heading hierarchy with correct levels
- ListVisitor extracts ordered and unordered list items
- TableVisitor extracts table rows and headers
- CodeBlockVisitor extracts fenced code blocks with language annotations
- QuoteVisitor extracts blockquote content
- Empty token list handled without exceptions

### Scenario 2: Rule Engine & Rule Pack Loading

```bash
pytest tests/unit/test_engine_rule.py -v
```

**Expected outcome**: All tests pass. Verifies that:
- RulePackLoader loads valid YAML rule packs
- Invalid rules are skipped with logged warning
- Missing rule pack file raises FileNotFoundError
- Rule matching selects highest priority rule on conflict (Q2)
- Content-hash IDs are deterministic and unique (Q1, FR-014)

### Scenario 3: Deterministic Engine Extraction

```bash
pytest tests/unit/test_deterministic_engine.py -v
```

**Expected outcome**: All tests pass. Verifies that:
- DeterministicSemanticEngine conforms to SemanticExtractionEngine Protocol (FR-001)
- Documents with headings, lists, tables, code blocks, blockquotes produce appropriate elements (FR-004)
- Same document processed twice produces byte-identical output (FR-011)
- Evidence references include document_id, section_id, text, and rule_id (FR-008)
- Confidence scores match RFC-031 table (FR-009)
- ProcessingStats are reported (Q3, FR-014)
- Document with no recognizable patterns returns empty ExtractionResult
- Binary content is skipped with logged warning

### Scenario 4: Pattern Library & Built-in Rules

```bash
pytest tests/unit/test_engine_patterns.py -v
```

**Expected outcome**: All tests pass. Verifies that:
- Default rule pack is loaded and all FR-006 patterns are recognized
- User Story pattern produces type "entity" with confidence 0.95
- GWT pattern produces type "fact" with confidence 0.85
- Requirement statements produce type "fact" with confidence 0.70
- Business Rules produce type "fact" with confidence 0.70
- Custom rule pack with higher priority overrides built-in rules (FR-013)

### Scenario 5: Pipeline Integration

```bash
pytest tests/integration/test_deterministic_pipeline.py -v
```

**Expected outcome**: All tests pass. Verifies that:
- Factory resolves "none" to DeterministicSemanticEngine (FR-001)
- Pipeline invokes only SemanticExtractionEngine interface (F27 Layer Independence)
- ExtractionResult matches F27 canonical model (FR-001)
- Full pipeline executes without network access (FR-002)

### Scenario 6: All Tests

```bash
pytest tests/
```

**Expected outcome**: All existing F01–F27 tests pass — no regressions.

## Contracts Reference

- [Deterministic Engine Interface](contracts/deterministic-engine-interface.md) — Engine interface, configuration, and internal component contracts
- [Rule Pack Schema](contracts/rule-pack-schema.md) — Rule pack YAML format and validation rules

## Data Model Reference

- [Data Model](data-model.md) — DeterministicSemanticEngine, ExtractionState, Observation, ExtractionRule, RulePack, EvidenceReference, ProcessingStats
