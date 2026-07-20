# Feature Specification: Populate Stage Entities on Run Artifacts

**Feature Branch**: `032-populate-stage-entities`

**Created**: 2026-07-20

**Status**: Draft

**Input**: User description: "Analise o comando `specmetrics measure` e crie uma proposta de preenchimento dos 'entities' de cada json gerado em .specmetrics/runs/ pelo comando, posto que estes não estão com os seus dados populados."

## Clarifications

### Session 2026-07-20

- Q: Quando truncar em mais de N entities, quais devem ser mantidas? → A: Opção A — primeiros N por categoria para CSM/CFM, primeiros N global para demais stages. N configurável via config.yml, default 5000.

## User Scenarios & Testing

### User Story 1 - Analyst inspects a discover stage artifact (Priority: P1)

A requirements analyst runs `specmetrics measure` and opens `.specmetrics/runs/<id>/discover.json` to verify which specification documents were found in the project. The file shows not only the count but the actual document names and their relative paths, allowing the analyst to confirm the correct files were picked up by the adapters.

**Why this priority**: This is the most fundamental stage — if discovery data is missing, the user cannot validate that the correct specification documents entered the pipeline. Every downstream stage depends on this.

**Independent Test**: Can be tested by running `specmetrics measure` on a project with known specification files and verifying `discover.json` contains entries for each discovered document with its relative path and type.

**Acceptance Scenarios**:

1. **Given** a project with 3 `.sdd` specification files in subdirectories, **When** `specmetrics measure` completes, **Then** `discover.json` contains exactly 3 entries with filenames and relative paths.
2. **Given** a project with no specification files, **When** `specmetrics measure` completes, **Then** `discover.json` has `count: 0` and `entities: []`.

---

### User Story 2 - Analyst inspects an extract stage artifact (Priority: P1)

A measurement analyst opens `extract.json` to review what semantic elements were extracted from each document. Each entity entry shows the extracted element type, content snippet, confidence score, and the document+section it originated from, providing traceability into what the system understood from each specification.

**Why this priority**: Extracted elements are the foundation for all downstream analysis. Without this data, users cannot audit what the extraction engine produced, making measurement results opaque.

**Independent Test**: Can be tested by running on a specification file with known requirements and verifying `extract.json` contains elements with types matching the expected semantic categories (fact, entity, relationship, operation).

**Acceptance Scenarios**:

1. **Given** a specification containing a statement "the system MUST validate user identity", **When** extraction completes, **Then** `extract.json` contains a constraint-type element referencing the document and section where the text appears.
2. **Given** extraction encounters a document type it cannot process, **When** the stage completes, **Then** `extract.json` records the document path in `documents_skipped` entities.

---

### User Story 3 - Analyst inspects graph and model stage artifacts (Priority: P2)

A quality auditor opens `graph.json`, `csm.json`, and `cfm.json` to trace how raw extracted elements were organized into graph nodes and then classified into canonical specification/functional model entities. Every entity in each file preserves evidence references back to source documents.

**Why this priority**: These intermediate artifacts are critical for debugging classification quality and ensuring traceability. However, the count summaries alone provide less immediate value than the discover/extract data.

**Independent Test**: Can be tested by verifying that entity IDs in `cfm.json` can be cross-referenced with node IDs in `graph.json` and element IDs in `extract.json`.

**Acceptance Scenarios**:

1. **Given** a completed pipeline execution, **When** the user inspects `graph.json`, **Then** entities include node type (extracted_element/evidence), semantic type, and document+section evidence.
2. **Given** CSM classification identified a decision in the specification, **When** the user inspects `csm.json`, **Then** entities include the decision description, evidence reference, and rationale.
3. **Given** CFM classification identified an actor from the specification, **When** the user inspects `cfm.json`, **Then** entities include the actor name, type, and evidence reference.

---

### User Story 4 - Analyst inspects rule and measure stage artifacts (Priority: P2)

A measurement specialist opens `rule.json` to see which Rule Packs were applied and what modifications they made to the canonical model. Then opens `measure.json` to review each metric's total with its complexity breakdown by function type.

**Why this priority**: These stages produce the final outputs. The current measure.json already partially populates entities, but the rule.json and enriched measure entities provide the full picture.

**Independent Test**: Can be tested by applying a known Rule Pack and verifying `rule.json` contains an entity describing the applied rules and their effects.

**Acceptance Scenarios**:

1. **Given** a project with a Rule Pack that reclassifies certain data groups, **When** the rule stage completes, **Then** `rule.json` entities include the applied rules and the count of entities modified.
2. **Given** FPA measurement completes, **When** the user inspects `measure.json`, **Then** entities include not just metric totals but the complexity distribution and function type breakdown.

---

### User Story 5 - Analyst inspects export stage artifact (Priority: P3)

A CI/CD pipeline operator opens `export.json` to confirm that measurement results were exported to the expected files and formats.

**Why this priority**: The export stage is a convenience artifact. The primary export happens via the `--export` flag writing to `.specmetrics/output/`. The JSON artifact is supplementary.

**Independent Test**: Can be tested by running with `--export --format csv` and verifying `export.json` entities contain the exported file paths.

**Acceptance Scenarios**:

1. **Given** export to JSON format is enabled, **When** the pipeline completes, **Then** `export.json` entities contain the path of each exported file.

---

### Edge Cases

- What happens when a pipeline stage is skipped (e.g., `--from extract`)?
- How does the system handle empty results (no documents discovered, no elements extracted)?
- How does it handle very large entity sets beyond the configured truncation limit (e.g., 50k extracted elements with limit of 5000)?
- What happens when a document adapter fails mid-scan — are partial results recorded?
- How does the system represent entities for stages that didn't execute (failed/skipped)?
- How does the system avoid memory blowup when the extraction produces 100k+ elements?

## Constitution Check

**Engaged Principles**:
- **Principle V (Evidence First)**: Each entity in the artifacts MUST preserve evidence references back to source documents and sections, ensuring full traceability.
- **Principle VII (Canonical Representation)**: CSM and CFM entities MUST be serialized in their canonical form, not adapter-specific formats.
- **Principle XIV (Layer Independence)**: Each stage's entity serialization MUST be independent — discover entities do not depend on extraction or graph data.
- **Principle VI (Explainability by Design)**: Populated entities enable users to inspect and understand what each stage produced, making the pipeline explainable.
- **Principle VIII (Plugin-Oriented)**: Entity serialization for the extraction stage must accommodate arbitrary `ExtractionProvider` plugins without hardcoding provider-specific formats.

**Compliance Notes**:
- Entity evidence references must include graph node identifier, document identifier, section identifier, and the original text — preserving the evidence chain mandated by Principle V.
- CFM entity data must be serialized from the canonical functional model produced by the pipeline.
- The data model that carries stage outputs between pipeline execution and artifact serialization must be extended to include discovered documents, extracted elements, evidence graph metadata, and canonical specification model entities — none of which are currently available at serialization time.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST make available for each executed stage the entities it identified when writing the stage JSON artifact to `.specmetrics/runs/<id>/`. For the discover stage: discovered documents. For extract: extracted elements. For graph: graph nodes and edges. For csm: canonical specification model entities. For cfm: canonical functional model entities. For rule: applied rules metadata. For measure: metric results with breakdown. For export: exported file paths.
- **FR-002**: `discover.json` entities MUST contain each discovered document's `id`, `document_type`, and relative `path`. The `document_type` MUST be the type reported by the adapter (e.g., `"sdd"`, `"openspec"`, `"markdown"`).
- **FR-003**: `extract.json` entities MUST contain each extracted element's `id`, `type` (fact/entity/relationship/operation), `content` (first 200 characters), `confidence` score, and `evidence` with `document_id`, `section_id`, and `text` (first 200 characters). The total entity list under `entities` MUST be complemented with summary entries in `documents_processed` and `documents_skipped` sub-lists.
- **FR-004**: `graph.json` entities MUST contain each graph node with `id`, `node_type` (extracted_element/evidence), `semantic_type` (if applicable), `document_id`, `section_id`, and `text` (first 200 chars). Must also include an entity for the total `edge_count` and the graph `run_id`.
- **FR-005**: `csm.json` entities MUST contain each CSM entity categorized by type: `specification_activities`, `decisions`, `assumptions`, `constraints`, `risks`, `open_questions`, `acceptance_criteria`, `glossary_terms`, and `references`. Each entity must include its canonical fields (`id`, `description` truncado a 200 chars, `evidence_references`).
- **FR-006**: `cfm.json` entities MUST contain each CFM entity categorized by type: `actors`, `functional_processes`, `business_rules`, `data_groups`, `operations`, `relationships`, and `unclassified`. Each entity must include its canonical fields (`id`, `name`, `evidence`).
- **FR-007**: `rule.json` entities MUST contain the list of applied Rule Packs (`rule_pack_name`, `description`, `version`) and a summary of modifications (`entities_modified`, `vaf_applied`).
- **FR-008**: `measure.json` entities MUST include not only metric totals (existing behavior) but also a `breakdown` per-complexity-level or per-function-type for each metric that supports it (e.g., FPA breakdown by function type and complexity).
- **FR-009**: `export.json` entities MUST contain the list of exported file paths with their `format` (json/csv/xml) and `path` (relative to project root).
- **FR-010**: When a stage is skipped due to `--from` or a prior stage failure, its JSON file MUST still be written with `count: 0` and `entities: []`.
- **FR-011**: The system MUST support a configurable entity truncation limit defined in `config.yml` under a `run_artifacts.max_entities_per_stage` key, defaulting to 5000. When a stage produces more than this limit, the `entities` list MUST be truncated. For CSM and CFM stages, truncation MUST keep the first N entities per category (e.g., first 5000 decisions, first 5000 assumptions, etc.). For all other stages, truncation MUST keep the first N entities overall. The file MUST include a `_truncated: true` field at the end of the list along with `_total_count` indicating the actual total. The top-level `count` field MUST reflect the full total, not the truncated value.
- **FR-012**: The entities JSON files MUST remain backward-compatible — consumers reading older files with `entities: []` must not break. New fields in entity objects (`_truncated`, `_total_count`) are additive.

### Key Entities

- **Document**: Represents a specification file discovered by an adapter. Key attributes: unique identifier, relative path from project root, document type (adapter-reported type like "sdd" or "openspec"). Tracked by the discover stage.
- **ExtractedElement**: A semantic unit extracted from a document. Key attributes: `id`, `type` (fact/entity/relationship/operation), `content` (snippet), `confidence` (0-1), `evidence` (document_id, section_id, text). Tracked by the extract stage.
- **GraphNode / GraphEdge**: Nodes and edges forming the evidence graph. GraphNode has `node_type`, `semantic_type`, `document_id`, `section_id`, `text`. GraphEdge has `source`, `target`, `edge_type`. Tracked by the graph stage.
- **CSM Entity**: One of 9 specification-level categories (decisions, assumptions, constraints, risks, etc.). Each has `id`, `description`, `evidence_references`, `status`. Tracked by the csm stage.
- **CFM Entity**: One of 7 functional model categories (actors, processes, business rules, data groups, operations, relationships, unclassified). Each has `id`, `name`, `evidence`. Tracked by the cfm and rule stages.
- **Metric Result**: A measurement outcome. Key attributes: `metric` (name like "function_points"), `total` (score), `status`, `duration_ms`, plus optional `breakdown` by sub-category. Tracked by the measure stage.
- **Export File**: An output file produced by the export stage. Key attributes: `format` (json/csv/xml), `path` (relative to project root). Tracked by the export stage.

## Success Criteria

### Measurable Outcomes

- **SC-001**: After running `specmetrics measure`, every stage JSON file in `.specmetrics/runs/<id>/` has a non-empty `entities` array reflecting the data produced by that stage, not just the measure stage.
- **SC-002**: Each entity in `discover.json`, `extract.json`, and `graph.json` preserves at least one evidence reference (document_id + section_id + text) back to the source specification, satisfying the Evidence First principle.
- **SC-003**: Entity serialization for a stage with entities up to the configured truncation limit completes within 500ms per stage and produces a file no larger than the equivalent of 5000 full entities (approximately 5MB for richly detailed entities, less for simpler ones).
- **SC-004**: Backward compatibility is maintained — existing scripts that parse `.specmetrics/runs/<id>/*.json` and expect the `entities` array continue to work, with the same top-level keys (`name`, `count`, `count_type`, `duration_ms`, `entities`).
- **SC-005**: Each stage entity follows a consistent JSON schema where every object has an `id` field (when applicable) and any text/content fields are truncated to 200 characters for human readability.

## Assumptions

- Entity data for all stages is available within the system at the point where stage JSON artifacts are written.
- The data model used to carry stage results between pipeline execution and artifact serialization can be extended without breaking existing consumers.
- Truncation at 5000 entities per stage (configurable via `config.yml`) is acceptable — the full data lives in the graph store (`.specmetrics/evidence_graphs/`) and the canonical models; the run artifacts are summary files for human inspection.
- The export stage entity data will come from the list of exported files produced by the pipeline rather than from a handler-specific output.
- Document full content should NOT be included in entities to keep file sizes manageable — only metadata and path.
- No changes are required to the pipeline execution itself, only to the serialization layer and the `PipelineResult` data structure.
