# Quickstart: Specification Adapter Plugin Interface

## Prerequisites

- Python 3.12+
- Dependencies installed (`pytest`)
- F01 (Kernel & Pipeline Engine) implemented and tested
- F02 (Plugin Discovery & Registry) implemented and tested
- Test virtualenv activated

## Setup

```bash
source .venv/bin/activate
```

## Validation Scenarios

### Scenario 1: Adapter Interface Compliance

```bash
pytest tests/unit/test_adapter_interface.py -v
```

**Expected outcome**: All tests pass. Verifies that:
- The `SpecificationAdapter` Protocol requires `scan()` and `supports()` methods
- `Document` dataclass accepts valid fields
- Document validation rejects invalid inputs

### Scenario 2: Adapter Registry Lookup

```bash
pytest tests/unit/test_adapter_registry.py -v
```

**Expected outcome**: All tests pass. Verifies that:
- `AdapterRegistry.find_adapter()` returns the correct adapter for a path
- `AdapterRegistry.list_adapters()` returns all installed adapters
- No adapter matching returns `None`

### Scenario 3: F02 Plugin Integration

```bash
pytest tests/integration/test_adapter_pipeline.py -v
```

**Expected outcome**: All tests pass. Verifies that:
- A mock adapter packaged as an F02 plugin is discovered and registered
- The adapter is available via AdapterRegistry
- The adapter's `scan()` produces Documents consumed by the pipeline

### Scenario 4: All Tests

```bash
pytest tests/
```

**Expected outcome**: All previous F01, F02, and F03 tests pass — no
regressions.

## Contracts Reference

- [Adapter Interface Contract](contracts/adapter-interface.md) — How adapters
  must be structured and registered

## Data Model Reference

- [Data Model](data-model.md) — Document, DocumentSection, and AdapterRegistry
  definitions
