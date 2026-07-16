# Quickstart: OpenSpec Specification Adapter

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
pytest tests/unit/adapter/openspec/test_plugin.py -v -k "test_supports"
```

**Expected outcome**: `supports()` returns True for paths containing `openspec/specs/` and False for paths without it (SC-005).

### Scenario 2: Discover Current Specifications

```bash
pytest tests/unit/adapter/openspec/test_scanner.py -v -k "test_scan_specs"
```

**Expected outcome**: Given an OpenSpec repository with multiple domains, every `spec.md` under `openspec/specs/` is discovered and returned as a normalized `Document` with correct domain metadata.

### Scenario 3: Discover Active Changes

```bash
pytest tests/unit/adapter/openspec/test_scanner.py -v -k "test_scan_changes"
```

**Expected outcome**: Given a repository with active changes, all change artifacts (proposal.md, design.md, tasks.md, delta specs) are discovered. Each includes the change identifier in metadata (SC-004).

### Scenario 4: Empty Repository

```bash
pytest tests/unit/adapter/openspec/test_scanner.py -v -k "test_empty_repo"
```

**Expected outcome**: An empty `openspec/specs/` directory returns zero documents without error. Missing `changes/` directory is handled gracefully.

### Scenario 5: Malformed Document Handling

```bash
pytest tests/unit/adapter/openspec/test_scanner.py -v -k "test_malformed_files"
```

**Expected outcome**: Malformed Markdown files are included with available content. Corrupted UTF-8 files produce document-level errors without interrupting the scan (SC-003, FR-022).

### Scenario 6: Performance Benchmark

```bash
pytest tests/unit/adapter/openspec/test_scanner.py -v -k "test_benchmark"
```

**Expected outcome**: 500 Markdown artifacts scanned in under 5 seconds (SC-001).

### Scenario 7: Temp Folder Exclusion

```bash
pytest tests/unit/adapter/openspec/test_scanner.py -v -k "test_temp_folder_exclusion"
```

**Expected outcome**: `.git`, `__pycache__`, `.venv`, `node_modules`, `.specify`, and `_`-prefixed folders under `changes/` are excluded from discovery (FR-006).

## Contracts Reference

- [Adapter Interface Contract](contracts/adapter-interface.md) — SpecificationAdapter protocol, metadata contract, error handling

## Data Model Reference

- [Data Model](data-model.md) — Full entity definitions, metadata mappings, and discovery rules
