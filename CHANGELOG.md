# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]


## [0.4.0] — 2026-07-20

### [030-measure-metric-filter](specs/030-measure-metric-filter) Metric Filtering for `specmetrics measure` — filter by metric ID and migrate output to structured JSON

#### Added

- Add `metrics` positional argument to `measure` command — accepts `all`, `bcp`, `fpa`, `sfp`, `snap`, `sp`, `tshirt`, `tp`, `cp` as comma-separated values
- Add `_parse_metrics()` validation — deduplication, whitespace trimming, `all` override, invalid ID reporting
- Add `metrics_filter` field on `PipelineRequest` — passed through orchestrator to plugin discovery
- Add metric filtering in `PluginRegistry.install_handlers()` — skips measurement plugins not in the filter
- Add `_build_metric_results()`, `_build_stage_details()`, `_build_output_errors()`, `_get_llm_info()` helper methods on `PipelineOrchestrator`
- Add `_write_json_output()` — serializes `MeasureOutput` Pydantic model to `.specmetrics/output/specmetrics-output.json`
- Add Pydantic output models: `MeasureOutput`, `MeasureMetadata`, `MetricResult`, `StageInfo`, `ErrorRecord`
- Add `METRIC_NAME_MAP` and `METRIC_DISPLAY_MAP` constants for metric ID ↔ display name mapping
- Add `MetricOutputItem`, `StageOutputItem`, `ErrorOutputItem` dataclasses on `PipelineResult`
- Add 23 tests: `TestParseMetrics` (11), CLI argument (1), orchestrator filtering/output (7), contract schema (4)

#### Changed

- `run_measure()` accepts `metrics` parameter and passes `metrics_filter` to `PipelineRequest`
- `discover_plugins()` passes `metrics_filter` to handler installation
- `format_text_result()` displays all selected metrics with human-readable labels
- `_handle_export()` writes `specmetrics-output.json` instead of `specmetrics-output.text`

#### Fixed

- Fix plugin filtering mismatch — `CLI_ID_TO_PLUGIN_ID` reverse map converts `sp/tp/cp` to `storypoints/token_points/cognitive_points` so metric filter matches actual plugin registration IDs
- Fix `_build_stage_details` measure count — uses `metrics_filter` length instead of hardcoded `len(METRIC_NAME_MAP)` when filtering is active
- Fix `_get_llm_info` — defaults provider to `"none"` when no LLM configured; model key is omitted from JSON output when empty (deterministic mode)

### [029-deterministic-fallback-specialists](specs/029-deterministic-fallback-specialists) Specialized Deterministic Fallbacks — framework-specific rule packs for Speckit and OpenSpec repositories

#### Added

- Create `speckit_rules.yaml` and `openspec_rules.yaml` with rich regex patterns for full CFM and CSM extraction
- Create Speckit extraction rules: User Story headings, priority justification, GIVEN/WHEN/THEN acceptance scenarios, FR-NNN/SC-NNN requirement identifiers, Key Entities, Assumptions, Constitution Check, Edge Cases, task line activities, Actor extraction
- Create OpenSpec extraction rules: Requirement headings, DEVE/SHALL statements, Scenario/GIVEN/WHEN/THEN, capability IDs, Decision records, Risk/Trade-off markers, proposal context sections, delta spec detection, domain entity recognition
- Implement per-rule failure isolation — regex exceptions are caught per-rule without halting the pipeline
- Add per-document extraction success rate tracking with WARN logging below 99%
- Create cross-spec entity coverage validation script
- Add semver version metadata to both framework rule packs
- Generate rule pack documentation from YAML schemas

#### Changed

- Replace minimal heading-only rule packs with full framework-specific specialist content

### [031-measure-id-export](specs/031-measure-id-export) Measure ID & Export Commands — run tracking, persistence, and export from stored runs

#### Added

- Add `measure_id` and `measure_id_path` fields to `MeasureMetadata` output model
- Create `generate_measure_id()` utility producing timestamp-prefixed UUIDs (`YYYYMMDD-HHMMSS-<short-uuid>`)
- Create `save_run_artifacts()` function persisting per-stage JSON to `.specmetrics/runs/<measure-id>/`
- Create `read_run_artifacts()` and `list_measure_runs()` helpers for loading and discovering runs
- Implement tabular normalization helpers for CSV and XML export formats
- Wire measure ID generation and run persistence into `specmetrics measure` — prints Measure ID to stdout
- Inject `measure.id` and `measure.id_path` into `specmetrics-output.json`
- Add `export list` subcommand displaying available run IDs ordered by recency
- Implement `export run <measure-id>` with JSON (copy), CSV, and XML format support
- Implement `export run` (without arguments) auto-selecting the most recent run
- Add `--export` and `--format` flags to `specmetrics measure` for automatic post-measurement export
- Add error handling for nonexistent run IDs with available-run listing

### [032-populate-stage-entities](specs/032-populate-stage-entities) Populate Stage Entities on Run Artifacts — per-stage entity data in `.specmetrics/runs/<id>/*.json`

#### Added

- Add `RunArtifactsSettings` to config schema with configurable `max_entities_per_stage` (default 5000)
- Add `stage_entities` field to `PipelineResult` data model
- Create `_build_stage_entities()` method mapping `PipelineContext` data to per-stage entity dicts
- Implement discover entities: discovered documents with id, document_type, and relative path
- Implement extract entities: extracted elements with type, content (200-char truncated), confidence, and evidence references
- Implement graph entities: graph nodes with node_type, semantic_type, document_id, section_id, text; summary with edge_count and run_id
- Implement CSM entities: 9 categories (decisions, assumptions, constraints, risks, etc.) with per-category truncation
- Implement CFM entities: 7 categories (actors, functional_processes, business_rules, data_groups, etc.) with per-category truncation
- Implement rule entities: applied Rule Pack info with modification summary
- Implement measure entities: breakdown per-complexity-level and per-function-type
- Implement export entities: exported file paths with format
- Add 200-char truncation helper for description/text/content fields
- Handle skipped/failed stages with empty entities array
- Add logging for truncation events when entities exceed max limit

### [033-clean-command](specs/033-clean-command) Clean Command for Runs Housekeeping — automatic removal of old `.specmetrics/runs/` folders

#### Added

- Create `RunFolder` and `RetentionPolicy` dataclasses for run folder metadata
- Implement `discover_run_folders()` with naming pattern filtering (`YYYYMMDD-HHMMSS-*`) and timestamp-sorted ordering
- Implement `compute_retention()` with `keep_runs` + `keep_days` intersection logic (AND when both active, standalone when one is zero)
- Implement `delete_run_folders()` using `shutil.rmtree` with per-folder permission error handling
- Implement `dry_run()` with preview output listing each run-to-delete and summary counts
- Implement `clean_runs()` orchestration tying discovery, retention computation, and deletion into a single callable
- Create `specmetrics clean` CLI command with `--keep-runs` (default 90), `--keep-days` (default 30), `--dry-run`, `--verbose`, `--quiet`, and `--project-path` options
- Handle missing or empty `.specmetrics/runs/` directory with graceful message and exit 0
- Create 29 unit and CLI integration tests covering default behavior, custom retention, dry-run, edge cases

[Unreleased]: https://github.com/amaurycarvalho/specmetrics/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/amaurycarvalho/specmetrics/releases/tag/v0.4.0

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
