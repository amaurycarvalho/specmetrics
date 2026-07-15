# Quickstart: Plugin Discovery & Registry

## Prerequisites

- Python 3.12+
- Dependencies installed: `pytest`
- Project structured per [plan.md](plan.md)
- F01 (Kernel & Pipeline Engine) implemented and tested
- Test virtualenv activated

## Setup

```bash
# From repository root
source .venv/bin/activate
```

## Validation Scenarios

### Scenario 1: Plugin Discovery from Entry Points

```bash
pytest tests/unit/test_plugin_discovery.py -v
```

**Expected outcome**: All tests pass. Verifies that plugins declaring
`specmetrics.plugins` entry points are discovered and their metadata is
extracted correctly.

### Scenario 2: Plugin Validation

```bash
pytest tests/unit/test_plugin_validation.py -v
```

**Expected outcome**: All tests pass. Verifies that:
- Compatible plugins pass validation
- Incompatible API versions are rejected with clear error messages
- Missing required interfaces cause rejection
- Unparseable version strings are rejected

### Scenario 3: Plugin Registry Operations

```bash
pytest tests/unit/test_plugin_registry.py -v
```

**Expected outcome**: All tests pass. Verifies that:
- Plugins can be registered and looked up by event type
- Multiple handlers for the same event type are returned in registration order
- Empty query returns empty result
- Duplicate plugin IDs log a warning and use the last registration
- `install_handlers()` correctly populates F01's HandlerRegistry

### Scenario 4: End-to-End Plugin Lifecycle

```bash
pytest tests/integration/test_plugin_lifecycle.py -v
```

**Expected outcome**: All tests pass. Verifies that:
- A mock plugin package is discovered, validated, and registered
- A broken plugin is skipped while healthy plugins register normally
- The Pipeline Engine can retrieve handlers via the registry integration
- Error isolation works — one plugin failure does not affect others

### Scenario 5: Graceful Error Handling

```bash
pytest tests/ -v -k "error or skip or reject"
```

**Expected outcome**: Tests confirm that loading errors, validation failures,
and missing dependencies are handled gracefully without crashing the system.

## Contracts Reference

- [Plugin Entry Point Contract](contracts/plugin-entry-point.md) — How plugins
  declare themselves via Python Entry Points

## Data Model Reference

- [Data Model](data-model.md) — Full entity definitions, fields, and validation
  rules
