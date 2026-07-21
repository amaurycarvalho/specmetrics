# Feature Specification: Measure Metrics Breakdown

**Feature Branch**: `036-measure-metrics-breakdown`

**Created**: 2026-07-21

**Status**: Draft

**Input**: User description: "Adicione ao comando `measure` a geração do `runs/{measure id}/metrics.json` que conterá o detalhamento (breakdown) das pontuações das entidades de cada métrica processada. Avalie, com base no cálculo de cada métrica, quais dados entrarão no detalhamento. Este detalhamento deverá conter aberta a pontuação atribuida por entidade originadora da pontuação. O schema do detalhamento deverá o mesmo para todas as métricas envolvidas, de forma que possam ser importadas em dashboards com mais facilidade."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Metrics Breakdown File (Priority: P1)

As a platform user, when I run `specmetrics measure` on a project, I want a `metrics.json` file generated inside the run directory (`runs/<measure_id>/`) containing the per-entity breakdown of all metrics that were executed. This file allows me to inspect which specification entities contributed to each metric's total score and import the data into dashboards for analysis.

**Why this priority**: This is the core deliverable. Without this file, there is no per-entity visibility into metric scores. All downstream use cases (dashboards, audit, explainability) depend on this file existing.

**Independent Test**: Run `specmetrics measure` on any project with at least one metric enabled, then verify `runs/<measure_id>/metrics.json` exists and contains valid entries for each metric with their entities correctly attributed.

**Acceptance Scenarios**:

1. **Given** a project with specification files, **When** the user runs `specmetrics measure --metrics all`, **Then** the run directory contains `metrics.json` with one entry per enabled metric (fpa, sfp, snap, bcp, sp, tp, cp, tshirt), each containing the total score and a list of entities with their individual contributions.

2. **Given** a project with specification files, **When** the user runs `specmetrics measure --metrics fpa,sp`, **Then** `metrics.json` contains only entries for `fpa` and `sp` (story points), with no entries for the other metrics.

3. **Given** a project with specification files, **When** the user runs `specmetrics measure --metrics bcp` and the BCP SDK fails for some items, **Then** `metrics.json` still contains the BCP entry with `total` reflecting only successful items, and only successful items appear in the entities list. Failed items are reflected in the `warnings` array.

---

### User Story 2 - Uniform Schema Across All Metrics (Priority: P1)

As a dashboard consumer or data analyst, I want all metric entries in `metrics.json` to follow the same schema structure regardless of the metric type, so that I can write a single import/query logic that works for every metric without per-metric branching.

**Why this priority**: The uniform schema is the enabler for dashboards. Without it, per-metric data import requires custom logic, defeating the purpose of a consolidated breakdown file.

**Independent Test**: Generate `metrics.json` with at least three different metrics (e.g., FPA, Story Points, Token Points), then verify all entries share the same top-level keys (`name`, `metric`, `total`, `unit`, `entity_count`, `entities`, `metadata`), and all entity objects share the same keys (`id`, `name`, `type`, `score`, `metadata`).

**Acceptance Scenarios**:

1. **Given** `metrics.json` generated for all eight metrics, **When** a script iterates over all entries, **Then** every entry has the fields: `name`, `metric`, `total`, `unit`, `entity_count`, `entities`, and optionally `metadata`.

2. **Given** `metrics.json` generated for FPA and Token Points, **When** comparing entity objects between the two metrics, **Then** every entity has `id`, `name`, `type`, `score`, and optionally `metadata`. FPA-specific detail (complexity, DET count) and Token-Points-specific detail (weight, model_source) reside in the entity's `metadata` object.

3. **Given** `metrics.json` with all metrics, **When** a dashboard tool imports the file, **Then** it can produce a per-entity score table using the same query for every metric entry.

---

### User Story 3 - Explainability Through Entity Score Attribution (Priority: P2)

As a user auditing a measurement result, I want to trace back each entity's contribution to the total score, so I can understand why a specification element received a certain value and verify the calculation is correct.

**Why this priority**: While the breakdown file itself enables traceability, the actual value comes from ensuring the entity data includes sufficient context (name, type, metadata) to make the score understandable without consulting additional source files.

**Independent Test**: Open `metrics.json` for an FPA measurement. Verify each entity's `type` field uses canonical values (e.g., `data_group` or `operation`), and the metric-specific subclass (ILF, EIF, EI, EO, EQ) appears in `metadata.function_type`. The entity `name` should be human-readable.

**Acceptance Scenarios**:

1. **Given** `metrics.json` for an FPA measurement, **When** inspecting an entity of `type` "operation" with `metadata.function_type` "EI", **Then** the `score` equals the UFP weight (3, 4, or 6) and `metadata` contains `complexity`, `det_count`, and `ftr_count`.

2. **Given** `metrics.json` for Story Points, **When** inspecting a functional process entity, **Then** `metadata` contains `raw_score`, `normalized_value`, and `factor_breakdown` showing how each of the 6 factors contributed.

3. **Given** `metrics.json` for any metric, **When** an entity's `score` is zero, **Then** the entity is still listed (presence is significant), and `metadata` explains why the contribution was zero (e.g., element excluded by a rule).

---

### User Story 4 - Integration with Existing Run Artifacts (Priority: P2)

As a user who already relies on the existing run artifacts (e.g., `metadata.json`, `measure.json`), I want `metrics.json` to coexist with these files without duplicating or conflicting with their data, so the run directory remains a single source of truth.

**Why this priority**: The feature adds a new artifact; it must not break or confuse users relying on existing artifacts.

**Independent Test**: Run `specmetrics measure` and verify the run directory contains both the new `metrics.json` and all previously existing files (`metadata.json`, `discover.json`, `extract.json`, `graph.json`, `csm.json`, `cfm.json`, `rule.json`, `measure.json`, `export.json`). Verify no existing file has been modified or removed.

**Acceptance Scenarios**:

1. **Given** a run directory with `metadata.json` and stage JSON files, **When** `metrics.json` is generated, **Then** all existing files remain unchanged and the `measure.json` stage file continues to contain the aggregated measurement payload.

2. **Given** a run directory with `metrics.json`, **When** the user runs `specmetrics export run <measure_id> --format json`, **Then** the export process does not break due to the presence of the new file.

---

### Edge Cases

- What happens when a measurement plugin produces zero entities (e.g., an empty specification with no functional processes)?
  - `entity_count` is 0, `total` is 0, and `entities` is an empty array. The entry still exists for the metric.

- What happens when a metric's handler fails entirely (e.g., BCP SDK timeout)?
  - The metric entry includes `status: "failed"` and `errors` describing the failure. `total` is 0 and `entities` is an empty array.

- What happens when a metric is skipped due to `--metrics` filter?
  - The metric entry is simply absent from the array. No placeholder or empty entry is generated.

- What happens when the same entity contributes to multiple metrics?
  - Each metric independently lists the entity in its own `entities` array with the score relevant to that metric.

- What happens when a metric has entities from both CSM and CFM models (Token Points, Cognitive Points)?
  - Entities are listed in a single flat `entities` array regardless of source model. The `id` prefix (`cfm:` vs `csm:`) distinguishes the origin model, and the `type` field uses canonical categories.

- What happens with very large projects producing thousands of entities?
  - All entities are included without truncation. The `metrics.json` file is a complete source of truth. Performance scales linearly with entity count; the 200ms/500-entity target serves as a guideline. Consumers that need sampling or pagination should implement it at the import layer.

## Constitution Check *(mandatory)*

**Engaged Principles**:

- **IV - LLM-Assisted, Deterministic Results**: The `metrics.json` file records the output of deterministic measurement engines. The breakdown exposes the result of explicit counting rules applied to canonical entities.
- **V - Evidence First**: Each entity records its `id` referencing the originating CFM/CSM element, preserving the chain from specification to score.
- **VI - Explainability by Design**: The per-entity score attribution directly fulfills this principle, making every measurement traceable to its constituent entities.
- **VII - Canonical Representation**: The uniform schema operates on normalized metric outputs, not framework-specific artifacts.
- **XI - Observability as a Native Capability**: The `metrics.json` file is structured telemetry suitable for dashboard consumption.
- **XIV - Layer Independence**: The feature reads from the measurement layer (after deterministic engines) and writes to the publication layer (run artifacts). It does not bypass architectural boundaries.

**Compliance Notes**: All eight deterministic measurement engines already produce structured results with per-entity data. This feature only serializes that data into a uniform JSON artifact. No engine changes are required. The uniform schema normalizes metric-specific entity details into a common `metadata` envelope, respecting canonical isolation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `measure` command MUST generate a `metrics.json` file inside the run directory (`runs/<measure_id>/`) after all requested metrics have completed execution, as a new run artifact alongside existing stage files.
- **FR-002**: `metrics.json` MUST contain a JSON array with one entry per metric that was selected and successfully or partially executed during the measurement.
- **FR-003**: Each metric entry MUST include the following fixed fields: `name` (metric ID, e.g., "fpa"), `metric` (metric JSON name, e.g., "function_points"), `total` (aggregate score), `unit` (measurement unit, e.g., "ufp", "story_points", "tokens"), `entity_count` (number of entities), `entities` (array of entity objects).
- **FR-004**: Each entity object MUST include the following fixed fields: `id` (unique element identifier in compound URI format `<source_model>:<entity_category>:<element_name>`, e.g., `"cfm:data_group:user-profile"`), `name` (human-readable name), `type` (canonical entity category from the fixed vocabulary defined in Key Entities), `score` (numeric contribution to the total). Metric-specific subtypes (e.g., "ILF" within a data_group) MUST be placed in `metadata` rather than in `type`.
- **FR-005**: Each metric entry MAY include an optional `metadata` object and each entity object MAY include an optional `metadata` object, carrying metric-specific auxiliary data (e.g., complexity, weights, factor breakdowns).
- **FR-006**: The metric entry MUST include `status` ("success" or "failed") and MAY include `errors` (array of error strings) and `warnings` (array of warning strings) for metrics that partially or fully failed.
- **FR-007**: The `metrics.json` file MUST be generated regardless of whether the measurement was successful, partial, or failed, reflecting whatever data was available.
- **FR-008**: The `metrics.json` schema MUST be identical for all metric types; no metric-specific top-level or entity-level keys other than `metadata`.
- **FR-009**: The system MUST serialize all metric-level `metadata` and entity-level `metadata` as flat JSON objects (no nested `metadata.metadata`), with keys named according to each metric's domain terminology.
- **FR-010**: The `metrics.json` file MUST use UTF-8 encoding with pretty-printed JSON (indentation).

### Key Entities

- **MetricBreakdownEntry**: Represents one metric's measurement result. Contains `name`, `metric`, `total`, `unit`, `entity_count`, `entities`, optional `status`, `errors`, `warnings`, and `metadata`.
- **EntityScore**: Represents one entity's contribution to a metric's total score. Contains `id` (compound URI `<source_model>:<entity_category>:<element_name>`), `name` (human-readable name), `type` (canonical entity category), `score` (numeric contribution), and optional `metadata`. The `id` encodes the origin model (`cfm` for Canonical Functional Model, `csm` for Canonical Specification Model) and element identity, enabling direct lookup in the corresponding model artifact. The `type` field MUST use one of the canonical types listed below; metric-specific sub-classifications (e.g., "ILF" vs "EIF" within data groups) reside in `metadata`.
- **CanonicalEntityType**: Fixed vocabulary shared by all metrics. Valid values: `data_group`, `operation`, `functional_process`, `specification_activity`, `business_rule`, `actor`, `relationship`, `decision`, `assumption`, `constraint`, `risk`, `open_question`, `acceptance_criteria`, `glossary_term`. Each metric maps its internal element types to the nearest canonical type.
- **MetricMetadata**: Optional key-value data specific to a metric (e.g., for FPA: `vaf`, `method` "ifpug"; for SFP: `contributions`; for Story Points: `scale` "fibonacci").
- **EntityMetadata**: Optional key-value data specific to an entity (e.g., for FPA entities: `function_type` "ILF", `complexity` "Low", `det_count`, `ret_count`, `ftr_count`; for Story Points entities: `raw_score`, `normalized_value`, `factor_breakdown`).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Running `specmetrics measure` on a project with at least one functional process produces `metrics.json` with `entity_count > 0` for every enabled metric that found applicable entities.
- **SC-002**: A dashboard tool can import `metrics.json` for any combination of metrics using a single schema definition, without per-metric column mapping.
- **SC-003**: Every entity's `score` field in `metrics.json` matches the value computed by its respective deterministic measurement engine, verified by comparing against individual engine outputs.
- **SC-004**: The `metrics.json` file generation adds no more than 200ms to the total measurement execution time for projects with up to 500 entities across all metrics. Performance scales linearly for larger entity counts.
- **SC-005**: Users can trace a specific entity's score from `metrics.json` back to the corresponding specification evidence by following the entity `id` to the canonical model artifacts stored in the same run directory, fulfilling the evidence chain requirement.

## Clarifications

### Session 2026-07-21

- Q: Should the entity `type` field use a fixed canonical set shared across all metrics, or per-metric free-form? → A: Fixed canonical set — all entities map to a shared vocabulary regardless of metric origin.
- Q: What format should the entity `id` field follow? → A: Compound URI `<source_model>:<entity_category>:<element_name>` (e.g., `"cfm:data_group:user-profile"`, `"csm:risk:security-scan"`).
- Q: How should the system handle very large entity counts? → A: No truncation — `metrics.json` always includes all entities. File size is the consumer's responsibility; the performance target scales linearly.

## Assumptions

- All metric plugins already store sufficient per-entity data during measurement to populate the `metrics.json` breakdown. No engine-level changes are needed; only serialization logic needs to be added.
- The `run_measure()` function in `cli/measure.py` is the appropriate integration point, specifically within or alongside `save_run_artifacts()`.
- The uniform schema normalization (metric-specific fields into `metadata`) is acceptable even if it dilutes the schema strictness slightly, since the trade-off enables dashboard uniformity.
- The `measure.json` stage file will continue to hold the raw aggregated payload from all handlers; `metrics.json` is an additional structured artifact derived from the same data.
- The existing `--metrics` filter and `--stage` filter already limit which metrics execute, so `metrics.json` naturally reflects only executed metrics.
- BCP and TShirt metrics will include only successful entities; failed BCP SDK calls will be reflected in `errors`/`warnings` at the metric entry level.
