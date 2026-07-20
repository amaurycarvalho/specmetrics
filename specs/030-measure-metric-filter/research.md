# Research: Measure Metric Filtering & JSON Output

## Overview

Research findings and technology decisions for adding metric selection filtering to the `specmetrics measure` command and migrating the output file to structured JSON.

## Decisions

### Decision: Typer `Optional[str]` argument for metric list

**Rationale**: Typer natively supports optional positional arguments. Using `Optional[str]` with a default of `None` (meaning `all`) is the simplest approach. The argument is parsed and validated inside `run_measure()`, splitting by comma and trimming whitespace. This avoids overloading Typer's internal argument parsing with custom types.

**Alternatives considered**:
- Custom Typer `click.ParamType` — adds complexity without benefit for simple string parsing
- Multiple positional arguments via `List[str]` — Typer does not natively support variable-length positional args cleanly
- `--metrics` flag instead of positional — less ergonomic; positional matches the `specmetrics measure fpa, sfp` syntax requested in the spec

### Decision: Metric filter applied at orchestrator level

**Rationale**: The orchestrator (`PipelineOrchestrator`) already discovers and invokes measurement plugins via the event-driven pipeline. A `metrics_filter: list[str] | None` field on `PipelineRequest` tells the orchestrator which plugin IDs to invoke. If `None` or `["all"]`, all plugins execute. This keeps filtering logic centralized and preserves Layer Independence (XIV) — individual measurement plugins are never aware of filtering.

**Alternatives considered**:
- CLI-level loop invoking measure per metric — duplicates pipeline setup, loses shared stage execution
- Kernel-level filter — violates Layer Independence (XIV) by pushing orchestration concern into the kernel
- Plugin-level self-selection — each plugin would need to check a filter, violating Plugin Isolation

### Decision: JSON output via `json.dumps()` with Pydantic model validation

**Rationale**: The new `specmetrics-output.json` schema has nested structure with specific fields. Pydantic v2 models provide schema validation, serialization, and self-documentation. The JSON is written atomically to `.specmetrics/output/specmetrics-output.json`. Using Pydantic ensures the output always conforms to the spec schema.

**Alternatives considered**:
- Plain dict with `json.dumps()` — no schema enforcement, risk of drift from spec
- JSON exporter plugin — overkill for a single mandatory output format; exporter plugins are for optional user-selected formats
- Structured logging via structlog — loses the file-based persistence requirement

### Decision: Snake_case metric names mapped from plugin entry point IDs

**Rationale**: The JSON `results[].name` field must use snake_case (e.g., `function_points`, `business_complexity_points`). Each measurement plugin's entry point ID (e.g., `fpa`, `bcp`) maps to a canonical name via a lookup table. This decouples the CLI metric short-name (`fpa`) from the JSON output name (`function_points`), allowing plugins to be renamed without breaking the output schema.

**Alternatives considered**:
- Using plugin entry point names directly — entry point IDs are short codes, not descriptive enough for JSON output
- Using plugin metadata `name` field — less stable; plugins could change display names
- Auto-generating from entry point ID — `fpa` → `fpa` is not descriptive; explicit mapping is clearer

### Decision: Text output preserves existing format, extends with all metrics

**Rationale**: FR-009 requires backward-compatible text output that shows sub-details as today. The current text format shows only FPA results. The new text output iterates over all selected metrics and displays their totals alongside the existing FPA breakdown. This prevents breaking existing users while adding new information.

**Alternatives considered**:
- Replacing FPA-centric output with a new format — breaks existing tooling and user expectations
- Conditionally showing metrics based on filter — inconsistent behavior between `all` and filtered modes

### Decision: `specmetrics-output.text` replaced by `specmetrics-output.json` unconditionally

**Rationale**: The spec explicitly states the `.text` file is replaced by `.json`. When `output_format` is `TEXT` (the default), the pipeline writes `specmetrics-output.json` to `.specmetrics/output/` in addition to printing formatted text to stdout. The old `str(result_data)` text file format is removed entirely.

**Alternatives considered**:
- Writing both `.text` and `.json` — violates spec requirement; unnecessary duplication
- Configurable output file format — adds complexity; the spec mandates JSON as the new default

## Dependencies

### Existing (reuse)

| Dependency | Usage |
|---|---|
| Typer | CLI argument parsing |
| Pydantic v2 | JSON output schema models |
| Plugin discovery (entry points) | Metric ID → plugin resolution |
| Pipeline Orchestrator | Central execution coordination |

### New (if any)

No new external dependencies required. All logic is custom, extending existing infrastructure.

## Integration Points

| Interface | Direction | Purpose |
|---|---|---|
| CLI (`specmetrics measure [metrics]`) | User → System | Optional metric selection |
| `PipelineRequest.metrics_filter` | CLI → Orchestrator | Metric selection payload |
| Plugin registry (entry points) | Orchestrator → Plugin | Resolve metric IDs to plugins |
| `formatters.py` | System → User | Text output with all selected metrics |
| `specmetrics-output.json` | System → File | Structured JSON output |
