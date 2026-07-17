# Quickstart: SpecKit Specification Adapter

## Prerequisites

- Python 3.13+
- Dependencies installed: `structlog`
- Project structured per `plan.md`

## Setup

```bash
# From repository root
uv sync  # or: pip install -e .
```

## Validation Scenarios

### Scenario 1: Repository Detection

```bash
pytest tests/unit/adapter/speckit/test_speckit_plugin.py -v -k "test_supports"
```

**Expected outcome**: `supports()` returns True for paths containing `.specify/`, `.specify/memory/constitution.md`, or `specs/`. Returns False for paths without any SpecKit marker.

### Scenario 2: Discover Governance Documents

```bash
pytest tests/unit/adapter/speckit/test_speckit_scanner.py -v -k "test_scan_governance"
```

**Expected outcome**: Given a repository with `.specify/memory/constitution.md`, the document is discovered and normalized with `kind: governance` and `feature: null` (FR-003, SC-004).

### Scenario 3: Discover Feature Workspaces

```bash
pytest tests/unit/adapter/speckit/test_speckit_scanner.py -v -k "test_scan_features"
```

**Expected outcome**: Given multiple feature directories under `specs/`, all artifact files (spec.md, plan.md, tasks.md, etc.) are discovered. Each document includes the correct feature identifier and workspace path (FR-004, SC-004).

### Scenario 4: Empty Repository

```bash
pytest tests/unit/adapter/speckit/test_speckit_scanner.py -v -k "test_empty_repo"
```

**Expected outcome**: Empty `.specify/memory/` returns zero governance documents. Empty `specs/` returns zero feature artifacts. No errors generated.

### Scenario 5: Optional Artifacts

```bash
pytest tests/unit/adapter/speckit/test_speckit_scanner.py -v -k "test_optional_artifacts"
```

**Expected outcome**: A feature containing only `spec.md` returns exactly one document. Missing optional artifacts (plan.md, tasks.md, etc.) do not cause errors (Edge Cases).

### Scenario 6: Unknown Markdown Files

```bash
pytest tests/unit/adapter/speckit/test_speckit_scanner.py -v -k "test_unknown_files"
```

**Expected outcome**: Custom `.md` files inside feature folders (e.g., `notes.md`) are included with `document_type: unknown` and `kind: unknown` (FR-007).

### Scenario 7: Malformed Document Handling

```bash
pytest tests/unit/adapter/speckit/test_speckit_scanner.py -v -k "test_malformed_files"
```

**Expected outcome**: Malformed Markdown files are included with available content. Corrupted UTF-8 files produce document-level errors without interrupting the scan (SC-003, FR-023).

### Scenario 8: Performance Benchmark

```bash
pytest tests/unit/adapter/speckit/test_speckit_scanner.py -v -k "test_benchmark"
```

**Expected outcome**: 500+ Markdown artifacts scanned in under 5 seconds (SC-001).

## Contracts Reference

- [Adapter Interface Contract](contracts/adapter-interface.md) — SpecificationAdapter protocol, metadata contract, error handling

## Data Model Reference

- [Data Model](data-model.md) — Full entity definitions, metadata mappings, and discovery rules
