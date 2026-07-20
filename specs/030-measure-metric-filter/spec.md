# Feature Specification: Measure Metric Filtering & JSON Output

**Feature Branch**: `030-measure-metric-filter`

**Created**: 2026-07-20

**Status**: Draft

**Input**: User description: "Adicione a sintaxe abaixo ao comando `measure` para permitir focar a análise em uma metrica, algumas metricas ou todas. `specmetrics measure [all|bcp|fpa|sfp|snap|sp|tshirt|tp|cp [, ...]]`. `all` é o default. O `Results`, após a execução do measure, deverá exibir o total para cada metrica selecionada. O `specmetrics-output.text` deverá ser gerado como `specmetrics-output.json` (formato json)."

## User Scenarios & Testing

### User Story 1 — Run Measurement with Default (All Metrics) (Priority: P1)

A quality engineer runs `specmetrics measure` (or `specmetrics measure all`) on their project and gets results for all 8 metrics. The output displays the total for each metric and a JSON file is written with the complete structured result.

**Why this priority**: This is the default behavior that every user will experience when running the measure command. It preserves backward compatibility and covers the primary use case.

**Independent Test**: Can be fully tested by running `specmetrics measure` on a known test project and verifying that all 8 metric lines appear in the Results section and a `specmetrics-output.json` file is generated.

**Acceptance Scenarios**:

1. **Given** a valid project, **When** the user runs `specmetrics measure`, **Then** the CLI prints results for all 8 metrics (BCP, FPA, SFP, SNAP, Story Points, T-Shirt, Token Points, Cognitive Points) with their totals
2. **Given** a valid project, **When** the user runs `specmetrics measure all`, **Then** the CLI prints results for all 8 metrics, identical to running `specmetrics measure` without arguments
3. **Given** a valid project, **When** the user runs `specmetrics measure`, **Then** a `specmetrics-output.json` file is created in `.specmetrics/output/` with the complete JSON result structure

---

### User Story 2 — Filter to a Single Metric (Priority: P1)

A quality engineer wants to focus on a specific metric, e.g., `specmetrics measure fpa`, and sees only the Function Points result. This reduces execution time by skipping other metric calculations and produces focused output.

**Why this priority**: Selective metric execution is the core new capability. Running only needed metrics saves time and reduces noise in the output.

**Independent Test**: Can be tested by running `specmetrics measure fpa` and verifying that only the FPA metric is calculated and displayed, and other metrics are not executed.

**Acceptance Scenarios**:

1. **Given** a valid project, **When** the user runs `specmetrics measure fpa`, **Then** the CLI executes only the FPA metric and displays only the Function Points result
2. **Given** a valid project, **When** the user runs `specmetrics measure bcp`, **Then** the CLI executes only the BCP metric and displays only the Business Complexity Points result
3. **Given** a valid project, **When** the user runs `specmetrics measure sp`, **Then** the CLI executes only the Story Points metric and displays only the Story Points result

---

### User Story 3 — Filter to Multiple Metrics (Priority: P1)

A quality engineer wants to run a subset of metrics, e.g., `specmetrics measure fpa, sfp, snap`, and sees only the results for those three metrics. Metrics not listed are skipped.

**Why this priority**: The ability to select any combination of metrics is the primary flexibility use case. Power users and CI pipelines benefit from targeting specific measurement types.

**Independent Test**: Can be tested by running `specmetrics measure fpa, sfp` and verifying that FPA and SFP results are displayed, while other metrics are not.

**Acceptance Scenarios**:

1. **Given** a valid project, **When** the user runs `specmetrics measure fpa, sfp`, **Then** the CLI executes only FPA and SFP and displays their results
2. **Given** a valid project, **When** the user runs `specmetrics measure snap, sp, tshirt`, **Then** the CLI executes only SNAP, Story Points, and T-Shirt and displays their results
3. **Given** a valid project, **When** the user runs `specmetrics measure tp, cp`, **Then** the CLI executes only Token Points and Cognitive Points and displays their results

---

### User Story 4 — Invalid Metric Name Handling (Priority: P2)

A quality engineer accidentally types an invalid metric name, e.g., `specmetrics measure invalid_metric`, and receives a clear error message listing the valid metric names.

**Why this priority**: Defensive error handling ensures users understand the available options without consulting documentation. This prevents confusion and support requests.

**Independent Test**: Can be tested by running `specmetrics measure invalid_name` and verifying a descriptive error message is shown.

**Acceptance Scenarios**:

1. **Given** the CLI, **When** the user runs `specmetrics measure unknown`, **Then** the CLI prints an error listing valid metric names (all, bcp, fpa, sfp, snap, sp, tshirt, tp, cp)
2. **Given** the CLI, **When** the user runs `specmetrics measure fpa, unknown`, **Then** the CLI prints an error before any metric execution, indicating the invalid metric name
3. **Given** the CLI, **When** the user runs `specmetrics measure` with an empty metric list, **Then** the CLI defaults to `all` and executes all metrics

---

### Edge Cases

- What happens when the user passes multiple metrics with spaces vs commas? Both `fpa, sfp` and `fpa,sfp` should be accepted (whitespace around commas is trimmed).
- What happens when `all` is combined with specific metrics (e.g., `all, fpa`)? The `all` keyword makes the list redundant — the system treats it as `all` and executes every metric.
- What happens when the same metric is listed multiple times (e.g., `fpa, fpa`)? Duplicates should be ignored — each metric is executed only once.
- What happens when no metrics are available due to plugin failures? The CLI should report which metrics failed to load and exit with a non-zero code.
- What happens when the `specmetrics-output.json` file already exists? It should be overwritten with the new result.
- What happens when one selected metric fails (e.g., BCP LLM timeout) while others succeed? The command completes successfully with partial results — the failed metric is omitted from results and the error is recorded in the JSON `errors` array with exit code 0.
- What happens when `--stage measure` is combined with `fpa, sfp`? Only the measure stage runs, and only the FPA and SFP metrics are calculated within it.
- What happens when `--stage discover` is combined with `fpa`? The `--stage` flag determines which pipeline stage runs; metric filtering only applies to the measurement stage — other stages are unaffected.

## Constitution Check

**Engaged Principles**:

- **I (Specification First)** — The measure command consumes specifications as input; metric filtering does not change this.
- **VII (Canonical Representation)** — Metric filtering operates at the measurement orchestration level, not on individual measurement engines, preserving canonical isolation.
- **VIII (Plugin-Oriented)** — Metrics are already plugins. The filtering feature selects which measurement plugins to invoke, respecting the plugin architecture.
- **X (AI-Friendly by Design)** — The JSON output format makes results machine-consumable by AI agents and CI pipelines.
- **XI (Observability as a Native Capability)** — Structured JSON output with metadata (sdd_framework, LLM info, timestamps, duration per metric) enables observability integration.
- **XIV (Layer Independence)** — Metric filtering is a CLI/orchestration concern and does not affect individual measurement engine implementations.

**Compliance Notes**: Principle VII is satisfied because filtering selects which plugins to invoke but does not change how each plugin produces its result. Principle VIII is satisfied because metric identifiers map to registered plugin entry points. Principle X is satisfied by producing structured JSON output alongside human-readable text. Principle XIV is satisfied because filtering is implemented at the orchestration layer without modifying individual metric plugins or the canonical model.

## Requirements

### Functional Requirements

- **FR-001**: The `measure` command MUST accept an optional `--metrics` / `-m` option specifying which metrics to run, with the syntax `specmetrics measure --metrics metric1,metric2`
- **FR-002**: When no metric argument is provided, the command MUST default to `all` and execute all available measurement plugins
- **FR-003**: The command MUST support the following metric identifiers: `all`, `bcp`, `fpa`, `sfp`, `snap`, `sp` (story points), `tshirt`, `tp` (token points), `cp` (cognitive points)
- **FR-004**: When `all` is specified (either explicitly or by default), the command MUST execute every available measurement plugin regardless of any other metrics listed
- **FR-005**: The command MUST ignore duplicate metric identifiers (e.g., `fpa, fpa` executes FPA once)
- **FR-006**: The command MUST accept both comma-separated and space-separated metric lists, trimming whitespace around separators
- **FR-007**: When an unrecognized metric identifier is provided, the command MUST print a descriptive error message listing valid identifiers and exit with non-zero status code, before executing any measurement
- **FR-008**: When specific metrics are selected, the pipeline MUST skip the measurement stage for unselected metrics — only configured measurement plugins for selected metrics MUST be executed
- **FR-008b**: If a selected metric plugin fails at runtime, the command MUST continue executing the remaining selected metrics and include the error details in the JSON `errors` array; the exit code MUST be 0 (partial success is not a fatal error)
- **FR-009**: The CLI output (stdout) MUST display a `Results:` section with at minimum one line per selected metric showing the human-readable metric name and its total value; sub-details (e.g., ILF/EIF breakdown for FPA) MUST still be shown as they are today
- **FR-010**: For T-Shirt sizing, the result MUST display the size label (e.g., `TShirt M: 0`) and each line represents a different size bucket
- **FR-011**: The pipeline MUST write the output file as `specmetrics-output.json` (JSON format) instead of `specmetrics-output.text`
- **FR-012**: The JSON output file MUST follow the structure:
  ```json
  {
    "measure": {
      "sdd_framework": "speckit" | "openspec",
      "created": "<datetime>",
      "llm": { "provider": "...", "model": "..." },
      "project_path": "..."
    },
    "results": [
      { "name": "function_points", "total": 0, "status": "completed", "duration_ms": 10542 }
    ],
    "stages": [
      { "name": "discover", "count": 0, "count_type": "documents", "duration_ms": 0 }
    ],
    "errors": [  ]
  }
  ```
- **FR-013**: The JSON output MUST include one entry in `results` for each selected metric, where `name` uses snake_case metric identifiers (e.g., `function_points`, `business_complexity_points`, `story_points`)
- **FR-014**: The JSON output MUST include a `stages` array with one entry per pipeline stage executed, including stage name, item count, count type, and duration
- **FR-015**: The JSON output MUST include an `errors` array with any errors encountered during execution; if no errors occur, the array MUST be empty
- **FR-016**: The JSON output MUST include the `measure` metadata block with `sdd_framework` (detected from the project's SDD framework), `created` (ISO 8601 datetime), `llm` info (provider and model from config), and `project_path` (resolved project path)
- **FR-017**: The JSON output MUST be written to `.specmetrics/output/specmetrics-output.json`
- **FR-018**: When metric filtering is combined with `--stage` or `--from` flags, metrics MUST act as a sub-filter within the selected stage — e.g., `--stage measure fpa,sfp` runs only the measure stage with only FPA and SFP

### Key Entities

- **Metric Selection**: The set of metrics chosen by the user via CLI argument — controls which measurement plugins are invoked during pipeline execution
- **Pipeline Metric Filter**: Orchestration mechanism that receives the metric selection and configures the pipeline to execute only the corresponding measurement plugins
- **Measure Metadata Block**: Structured metadata about the measurement run including SDD framework detection, timestamp, LLM configuration, and project path
- **JSON Result Schema**: The structured output schema specifying the shape of `specmetrics-output.json`, with sections for measure metadata, results array, stages array, and errors array

## Success Criteria

### Measurable Outcomes

- **SC-001**: Running `specmetrics measure fpa` executes only the FPA measurement and completes in less time than running `specmetrics measure all` on the same project
- **SC-002**: Running `specmetrics measure` (default) produces identical metric results to running `specmetrics measure all`
- **SC-003**: The JSON output file at `.specmetrics/output/specmetrics-output.json` is valid JSON conforming to the defined schema for all valid metric selections
- **SC-004**: Invalid metric names produce a clear error message within 1 second, listing valid options
- **SC-005**: Running the same metric selection twice on an unchanged project produces identical results in both text output and JSON output
- **SC-006**: The text output's Results section contains exactly one line per selected metric, with totals matching the corresponding JSON `results[].total` values

## Clarifications

### Session 2026-07-20

- Q: When a selected metric plugin fails (e.g., BCP LLM timeout), should the entire command fail or complete with partial results? → A: Complete with partial results — execute remaining metrics, report errors in JSON `errors` array, exit code 0 (partial success).
- Q: How should metric filtering compose with `--stage` and `--from` flags? → A: Metrics are a sub-filter of stage selection — `--stage measure` + `fpa,sfp` runs only the measure stage with only those metrics.
- Q: Should text output show sub-details (ILF/EIF etc.) or totals only? → A: Show full detail always, same breakdown as today, backward compatible.

### Session 2026-07-20 (post-implementation)

- Q: The `metrics` argument was implemented as a positional argument. Should it remain positional or be a `--metrics` option? → A: Changed to `--metrics` / `-m` option after user feedback. Positional arguments cause ambiguity with `PROJECT_PATH` and break existing command patterns. The overlapping short IDs (`sp`, `tp`, `cp`) are not intuitive as positional args and an explicit `--metrics` flag provides clearer CLI semantics for optional selection.
- Q: Why were `results` empty when running `specmetrics measure . sp,tp,cp`? → A: The plugin registry filtered by `descriptor.metadata.id` (e.g., `storypoints`) but the CLI filter passed short IDs (e.g., `sp`). Fixed with `CLI_ID_TO_PLUGIN_ID` reverse map at `specmetrics/application/models.py`.
- Q: What should the `llm.provider` field contain when running without an API key (deterministic extraction)? → A: `"none"` with the `model` key omitted entirely from JSON output, since no LLM model was used.
- Q: How should display names appear in the text Results section when the metric is identified by its JSON snake_case name? → A: `METRIC_DISPLAY_MAP` is keyed by CLI short IDs (`bcp`, `fpa`), but `MetricOutputItem.name` stores the JSON snake_case name (`business_complexity_points`). Fixed by adding `JSON_NAME_TO_DISPLAY_MAP` (`{METRIC_NAME_MAP[k]: v for k, v in METRIC_DISPLAY_MAP.items()}`) and switching `format_text_result` to use it.
- Q: Should the text output show "items" or "metrics" for the measure stage count? → A: "metrics" — the measure stage processes metrics, not items. Updated `format_text_result` to use `label = "metrics" if sr.stage.value == "measure" else "items"`.
- Q: Why does the JSON `stages[].count` differ from the text stages for extract/graph/csm/cfm/rule? → A: `_build_stage_details` (JSON) was missing entity-count logic for those stages — only `discover` and `measure` had it. Fixed by copying the same counting logic from `_build_stage_results` into `_build_stage_details` for extract (via `ctx.extraction_result.total_elements`), graph (via `ctx.evidence_graph.node_count`), csm (via `sum(csm.metadata.element_counts.values())`), cfm and rule (via `sum(cfm.metadata.element_counts.values())`).
- Q: Why does `_build_stage_results.entities_found` for measure show the wrong count? → A: It used a chain of `mr.get(key, 0) or ...` looking for the first non-zero metric VALUE (e.g., total function points). Fixed to use the metric count: `len(metrics_filter) if metrics_filter else len(METRIC_NAME_MAP)`.
- Q: Why does `specmetrics export run` produce empty measurements even when `measure` found items? → A: Two separate issues: (1) `specmetrics export run` runs its own independent pipeline, it does not reuse the measure command's results. (2) The export only extracts measurements from `cfm.functional_processes` — if no graph nodes have `semantic_type == "operation"`, functional_processes is empty. Additionally, `_extract_measurements` in `exporter/orchestrator.py` hardcodes `functional_size=0.0` and `complexity=""`, never incorporating the metric results computed by the measure stage. This is pre-existing behavior, not introduced by this feature.

## Assumptions

- The existing measurement plugins (bcp, fpa, sfp, snap, storypoints, tshirt, token_points, cognitive_points) remain registered via Python entry points and are discoverable by the plugin system
- The `specmetrics-output.text` file is completely replaced by `specmetrics-output.json` — both files will not coexist
- The T-Shirt metric produces per-size results; the text output will show each size as a separate line (e.g., `TShirt XS: 0`, `TShirt S: 0`, etc.), while the JSON will represent it as a single result entry with the total count per size
- The SDD framework detection relies on the existing adapter layer (openspec or speckit) to determine which framework the project uses
- LLM provider and model information is already available from the configuration system (config llm)
- Pipeline stage information (name, count, count_type, duration_ms) is already tracked by the pipeline engine and available in the PipelineResult
- The `specmetrics-output.json` file is overwritten on each subsequent run — no history or versioning is maintained for the output file
