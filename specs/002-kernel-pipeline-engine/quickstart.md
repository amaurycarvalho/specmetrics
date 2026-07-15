# Quickstart: Kernel & Pipeline Engine

## Prerequisites

- Python 3.13+
- Dependencies installed: `structlog`, `pytest`
- Project structured per `plan.md`

## Setup

```bash
# From repository root
uv sync  # or: pip install -e .
```

## Validation Scenarios

### Scenario 1: Basic Pipeline Execution

```bash
# Run unit tests for the Pipeline Engine
pytest tests/unit/test_pipeline_engine.py -v
```

**Expected outcome**: All tests pass. Verifies that the engine publishes events
in the correct canonical order, creates unique execution IDs, and collects
pipeline context correctly.

### Scenario 2: Event Bus Delivery

```bash
pytest tests/unit/test_event_bus.py -v
```

**Expected outcome**: All tests pass. Verifies that events are delivered
synchronously and in-order to registered handlers, and that unregistered event
types raise an error.

### Scenario 3: Pipeline Context Immutability

```bash
pytest tests/unit/test_pipeline_context.py -v
```

**Expected outcome**: All tests pass. Verifies that Pipeline Context instances
are truly immutable (frozen), that `with_stage_output` returns a new instance,
and that previous context versions remain intact.

### Scenario 4: End-to-End Pipeline with Mock Stages

```bash
pytest tests/integration/test_pipeline_execution.py -v
```

**Expected outcome**: All tests pass. Verifies a pipeline configured with 2–3
mock stages executes in the correct order, produces a complete event log, and
reports `PipelineCompleted`.

### Scenario 5: Pipeline Failure Handling

```bash
pytest tests/integration/test_pipeline_execution.py -v -k "fail"
```

**Expected outcome**: Pipeline halts when a stage raises `StageError`. The
`PIPELINE_FAILED` event contains the originating stage name and error message.
No downstream stages execute.

## Contracts Reference

- [Event Handler Contract](contracts/event-handler.md) — Interface for pipeline stage plugins
- [Pipeline Events Catalog](contracts/pipeline-events.md) — All event types and payload schemas
- [Pipeline Context Contract](contracts/pipeline-context.md) — Execution state container

## Data Model Reference

- [Data Model](data-model.md) — Full field definitions and validation rules
