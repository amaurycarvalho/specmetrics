# Feature Specification: T-Shirt Sizing Improvements

**Feature Branch**: `041-tshirt-sizing`

**Created**: 2026-07-21

**Status**: Draft

**Input**: User description: "Levante como e calculada metrica Tshirt. Proponha melhorias para que essa metrica se torne mais realista, aplicavel e represente melhor a estimativa de esforco de implementacao relacionada as especificacoes speckit ou openspec analisadas pelo specmetrics. O objetivo e conseguir estabelecer um comparativo de esforco de implementacao entre as diferentes especificacoes, visando que com essa informacao disponivel o usuario possa posteriormente quebrar manualmente suas especificacoes para que estas tenham aproximadamente o mesmo nivel de esforco, e assim viabilizar que metricas de fluxo (ex: throughput, percentis) possam ser melhor aplicadas garantindo um fluxo previsivel em um sistema Kanban."

## Current State Analysis

### How T-Shirt Sizing Is Currently Calculated

The T-Shirt Sizing measurement engine consumes Story Points results (Modified Fibonacci: 1, 2, 3, 5, 8, 13, 20, 40, 100) from the measurement pipeline and maps each entity's normalized Story Point value to a T-shirt size category (XS, S, M, L, XL, XXL) using a configurable lookup table.

**Current mapping table**:

| Story Point Value | T-Shirt Size |
|---|---|
| 1 | XS |
| 2 – 3 | S |
| 5 – 8 | M |
| 13 | L |
| 20 | XL |
| 40 – 100 | XXL |

**Pipeline position**: T-Shirt Sizing executes after all measurement plugins via its own dedicated event (`TSHIRT_CLASSIFICATION_COMPLETED`), consuming Story Points results from the pipeline context.

**Output**: The measurement result includes `total_items` (count of entities classified), a `distribution` dict (count per size), and per-entity classification details (element ID, name, Story Point value, T-shirt size, mapping rule).

**Current limitations**:

1. **Misaligned mapping ranges**: The current mapping places Story Point value 8 in M (together with 5) and 13 alone in L, while 20 stands alone in XL and 40-100 fill XXL. This creates uneven and unintuitive groupings: M covers 5-8 (two distinct sizes), L covers 13 only (one value), XL covers 20 only, and XXL covers 40-100 (three values). The groupings do not distribute the Fibonacci scale evenly across the six T-shirt sizes.

2. **Total not visible in measure.json**: The aggregated `measure.json` output shows `"total": 0` for the T-Shirt metric because the orchestrator's key mapping expects a specific top-level payload key that the T-Shirt plugin does not emit. The actual total exists in the result but does not surface through the standard reporting pipeline.

3. **No breakdown in measure.json**: The `measure.json` file lacks per-size count breakdowns. Users cannot see at a glance how many entities fall into each T-shirt size without inspecting the detailed entity list.

4. **CLI display shows zero**: The command-line output always displays `TShirt: 0` regardless of the actual classification results, because the formatter reads the same missing key.

5. **No cross-specification comparability**: While individual entities are classified into sizes, there is no mechanism to compare T-shirt size distributions across different specifications. Users cannot answer "are the entities in specification A typically larger or smaller than those in specification B?"

6. **No documentation**: There is no RFC documenting the T-Shirt Sizing methodology, mapping rationale, or usage guidance for Kanban work item sizing.

## Proposed Improvements

### 1. Corrected Mapping Table

Replace the current mapping with evenly distributed groupings that map each Fibonacci value to the closest T-shirt size:

| Story Point Value | T-Shirt Size |
|---|---|
| 1 | XS |
| 2 – 3 | S |
| 5 | M |
| 8 – 13 | L |
| 20 – 40 | XL |
| 100 | XXL |

**Rationale**: This mapping distributes the 9 Fibonacci values across the 6 T-shirt sizes with logical groupings: the smallest values (1, 2-3) map to the smallest sizes (XS, S); the middle value (5) stands alone as M; the moderate values (8-13) form L; the large values (20-40) form XL; and the maximum (100) stands alone as XXL. This creates a more intuitive and actionable sizing scale.

### 2. Corrected measure.json Output

The `measure.json` entry for T-Shirt Sizing must properly report:
- `total`: The total number of entities analyzed (all entities that received a Story Point classification)
- `status`: Always `"completed"` when the pipeline runs successfully
- `duration_ms`: Execution duration in milliseconds
- `breakdown`: A nested object with one entry per T-shirt size, each containing a `count` field with the number of entities in that size

```json
{
  "metric": "tshirt",
  "total": 42,
  "status": "completed",
  "duration_ms": 15,
  "breakdown": {
    "XS": { "count": 3 },
    "S": { "count": 8 },
    "M": { "count": 12 },
    "L": { "count": 10 },
    "XL": { "count": 7 },
    "XXL": { "count": 2 }
  }
}
```

### 3. Corrected metrics.json Output

The `metrics.json` entry for T-Shirt Sizing must report:
- `total`: The number of entities analyzed
- `unit`: Always `"entities"`
- `entities`: Array of per-entity classifications (element ID, name, type, Story Point score, T-shirt size, mapping rule)
- `metadata`: Contains `scale` (the T-shirt scale string), `mapping` (the Story Point to T-shirt mapping used), and the mapping version

```json
{
  "name": "tshirt",
  "metric": "tshirt",
  "total": 42,
  "unit": "entities",
  "entities": [
    {
      "id": "cfm:functional_process:process-order",
      "name": "Process Order",
      "type": "functional_process",
      "story_point_value": 8,
      "tshirt_size": "L",
      "mapping_rule": "default: 8-13 → L"
    }
  ],
  "status": "success",
  "metadata": {
    "scale": "XS-S-M-L-XL-XXL",
    "mapping": {
      "XS": 1,
      "S": 3,
      "M": 5,
      "L": 8,
      "XL": 13,
      "XXL": 100
    }
  }
}
```

### 4. Corrected CLI Display

The CLI text output must show:
- The total number of entities analyzed as the T-Shirt metric value
- Below the total, a breakdown line showing the count per T-shirt size

Example display:
```
Results:
  ...
  TShirt: 42 entities
    XS: 3  S: 8  M: 12  L: 10  XL: 7  XXL: 2
```

### 5. Cross-Specification Comparability

With corrected outputs, users can compare T-shirt size distributions across specifications to assess relative effort. A specification with more XL/XXL entities represents higher overall implementation effort than one dominated by XS/S entities. This enables the Kanban practice of manually grouping similarly-sized work items for predictable flow.

Note: Specification decomposition into equal-effort work items is a manual Kanban practice. SpecMetrics provides the comparability data that enables this practice but does not implement automatic chunking or splitting.

### 6. Documentation (RFC)

Create a dedicated RFC document in `docs/rfcs/` that documents:
- The T-Shirt Sizing methodology and its relationship to Story Points
- The complete mapping table with rationale for each grouping
- The output formats (measure.json, metrics.json, CLI display)
- Guidance on using T-Shirt distributions for cross-specification comparison and Kanban work item sizing

## User Scenarios & Testing

### User Story 1 - Accurate T-Shirt Classification (Priority: P1)

As a project manager, I want each entity to be classified into the correct T-shirt size based on a well-distributed mapping from Story Points, so that the size labels meaningfully reflect relative implementation effort.

**Why this priority**: The mapping is the foundation of the T-Shirt metric. Without correct mapping, all downstream outputs are misleading.

**Independent Test**: Run T-Shirt Sizing on a specification where entities have known Story Point values across the full Fibonacci range. Verify each entity receives the correct T-shirt size according to the new mapping table.

**Acceptance Scenarios**:

1. **Given** an entity with Story Point value 1, **When** T-Shirt Sizing is calculated, **Then** the entity is classified as XS.
2. **Given** an entity with Story Point value 8, **When** T-Shirt Sizing is calculated, **Then** the entity is classified as L (not M as in the current mapping).
3. **Given** an entity with Story Point value 40, **When** T-Shirt Sizing is calculated, **Then** the entity is classified as XL (not XXL as in the current mapping).
4. **Given** entities with Story Point values 1, 2, 3, 5, 8, 13, 20, 40, 100, **When** T-Shirt Sizing is calculated, **Then** all 9 Fibonacci values are covered across the 6 T-shirt sizes.

---

### User Story 2 - Correct measure.json Output (Priority: P1)

As a user running specmetrics measure, I want the `measure.json` file to correctly report the T-Shirt total and breakdown by size, so I can see at a glance how entities distribute across sizes.

**Why this priority**: `measure.json` is the primary output artifact consumed by downstream tooling and dashboards. A total of 0 makes the metric invisible.

**Independent Test**: Run a full measurement pipeline on a specification. Inspect `measure.json` and verify the T-Shirt entry shows `total > 0` and `breakdown` contains all six sizes with correct counts.

**Acceptance Scenarios**:

1. **Given** a specification with 15 entities classified across all six T-shirt sizes, **When** the pipeline completes, **Then** `measure.json` contains a T-Shirt entry with `total: 15`, `status: "completed"`, and `duration_ms` > 0.
2. **Given** the same result, **When** inspecting `breakdown`, **Then** it contains entries for XS, S, M, L, XL, and XXL, each with a `count` field matching the actual entity distribution.
3. **Given** a specification with no Story Points result (empty or missing), **When** T-Shirt runs, **Then** `measure.json` shows `total: 0` with an empty `breakdown`.

---

### User Story 3 - Correct metrics.json Output (Priority: P1)

As a user inspecting detailed metrics, I want `metrics.json` to include per-entity T-shirt classifications with the mapping metadata, so I can trace each entity's classification and understand the scale used.

**Why this priority**: `metrics.json` provides the detailed, entity-level view needed for audits and traceability.

**Independent Test**: Run a measurement on a specification. Verify `metrics.json` contains a T-Shirt entry with `unit: "entities"`, per-entity details (ID, name, type, Story Point value, T-shirt size, mapping rule), and metadata with scale and mapping.

**Acceptance Scenarios**:

1. **Given** a specification with 5 entities, **When** the pipeline completes, **Then** `metrics.json` T-Shirt entry has `total: 5` and `entities` array with 5 elements, each containing `id`, `name`, `type`, `story_point_value`, `tshirt_size`, and `mapping_rule`.
2. **Given** the same result, **When** inspecting `metadata`, **Then** it contains `scale: "XS-S-M-L-XL-XXL"` and a `mapping` object showing the Story Point thresholds for each size.
3. **Given** an entity whose Story Point value does not match any mapping range, **When** `metrics.json` is generated, **Then** the entity's `tshirt_size` is `"UNKNOWN"` and `mapping_rule` indicates no match.

---

### User Story 4 - Correct CLI Display (Priority: P2)

As a CLI user, I want to see the T-Shirt total and size breakdown directly in the terminal output after measurement, so I can immediately understand the effort distribution without opening JSON files.

**Why this priority**: CLI display provides immediate feedback. However, the JSON outputs (US2, US3) are the authoritative data sources.

**Independent Test**: Run `specmetrics measure` on a specification. Verify the terminal output shows a non-zero T-Shirt total and a breakdown line with per-size counts.

**Acceptance Scenarios**:

1. **Given** a specification with 20 entities distributed across sizes, **When** measurement completes, **Then** the CLI output shows `TShirt: 20 entities` (not 0).
2. **Given** the same result, **When** inspecting the T-Shirt line, **Then** below it a breakdown shows counts per size in format `XS: N  S: N  M: N  L: N  XL: N  XXL: N`.

---

### User Story 5 - Cross-Specification T-Shirt Comparison (Priority: P2)

As a Kanban flow manager, I want to compare T-shirt size distributions across specifications, so I can identify whether one specification's entities are consistently larger (more XL/XXL) than another's and manually organize work items for predictable flow.

**Why this priority**: Cross-specification comparison is the strategic goal. It depends on correct outputs (US2-US4) being in place first.

**Independent Test**: Run T-Shirt Sizing on two specifications with different effort profiles. Verify the size distribution reflects the expected difference (e.g., a complex spec has proportionally more L/XL/XXL entities).

**Acceptance Scenarios**:

1. **Given** two specifications where one has double the total raw implementation effort of the other, **When** T-Shirt distributions are compared, **Then** the larger-effort specification has a higher proportion of L, XL, and XXL entities.
2. **Given** two specifications from different SDD frameworks (SpecKit and OpenSpec) with similar effort, **When** T-Shirt distributions are compared, **Then** the size distributions are similar (within 20% for each size category).

---

### User Story 6 - T-Shirt RFC Documentation (Priority: P2)

As a developer or team lead, I want a dedicated RFC documenting the T-Shirt Sizing methodology, mapping, outputs, and Kanban usage guidance, so I can understand and apply the metric correctly.

**Why this priority**: Documentation is essential for adoption and trust.

**Independent Test**: Open the T-Shirt RFC document. Verify it contains methodology description, mapping table, output format specifications, and Kanban guidance.

**Acceptance Scenarios**:

1. **Given** the T-Shirt RFC is opened, **When** reading the methodology section, **Then** it explains the relationship with Story Points and the mapping logic.
2. **Given** the RFC, **When** reading the mapping section, **Then** it documents the complete Story Point to T-shirt mapping table with rationale for each grouping.
3. **Given** the RFC, **When** reading the output section, **Then** it specifies the measure.json, metrics.json, and CLI display formats for T-Shirt.

---

### Edge Cases

- **No Story Points result available**: T-Shirt Sizing cannot classify without Story Points. Output shows `total: 0`, an empty breakdown, and a warning code `"NO_STORY_POINTS"`.
- **Entity with missing or invalid Story Point value**: Entity is skipped with a warning code `"MISSING_SP_VALUE"`, incrementing no count.
- **Entity with Story Point value outside all mapping ranges**: Entity receives classification `"UNKNOWN"` with mapping rule indicating no matching range. Counted in total but flagged.
- **Empty specification (zero entities)**: Output shows `total: 0` with an empty breakdown. No warning needed.
- **Custom mapping provided via configuration**: If a user provides an alternative mapping table, it overrides the default. Validation ensures no overlapping or invalid ranges.
- **Large specifications (500+ entities)**: Classification scales linearly. All entities are processed and counted.

## Constitution Check

**Engaged Principles**:

- **IV - LLM-Assisted, Deterministic Results**: T-Shirt classification is a pure lookup-table operation — no LLM participates. Given the same Story Point value and mapping, the same T-shirt size is always returned.
- **V - Evidence First**: Each entity's classification preserves its Story Point value and the mapping rule applied, enabling traceability to the source estimation.
- **VI - Explainability by Design**: The mapping rule (e.g., `"default: 8-13 → L"`) is included in every entity output. Users can see exactly why an entity received its size.
- **VII - Canonical Representation**: T-Shirt operates on the Story Points result from the pipeline context. It does not depend on SpecKit, OpenSpec, or any framework-specific format.
- **VIII - Plugin-Oriented Architecture**: T-Shirt Sizing is a standalone measurement plugin. All changes are contained within `specmetrics/plugins/measurement/tshirt/`.
- **IX - Rule Externalization**: The mapping table (Story Point ranges to T-shirt sizes) is externalized as a configuration. Custom mappings can be provided.
- **XIII - Evolution Without Disruption**: Changing the default mapping values does not invalidate previously generated T-Shirt classifications. Each classification records its mapping rule.
- **XIV - Layer Independence**: T-Shirt depends only on the Story Points result from the pipeline context (already normalized through canonical models).

**Compliance Notes**: The feature corrects the default mapping table and fixes output integration issues. No new plugins, no new event types, no changes to the core pipeline. All modifications are within the existing T-Shirt plugin.

## Requirements

### Functional Requirements

- **FR-001**: The default mapping table MUST be updated to: XS=[1], S=[2,3], M=[5], L=[8,13], XL=[20,40], XXL=[100].

- **FR-002**: The `measure.json` output MUST include `total` equal to the total number of entities analyzed, `status` set to `"completed"`, `duration_ms` as execution time, and a `breakdown` object with one entry per T-shirt size containing a `count` field.

- **FR-003**: If no Story Points result is available, `measure.json` MUST show `total: 0` with an empty `breakdown`.

- **FR-004**: The `metrics.json` output MUST include `total` as the number of entities, `unit` set to `"entities"`, an `entities` array with per-entity details (`id`, `name`, `type`, `story_point_value`, `tshirt_size`, `mapping_rule`), and `metadata` containing `scale` and `mapping`.

- **FR-005**: The `metrics.json` `metadata.mapping` object MUST report the highest Story Point value in each T-shirt size range as the representative value (e.g., XS→1, S→3, M→5, L→8, XL→13, XXL→100).

- **FR-006**: The CLI display MUST show the T-Shirt total as the number of entities analyzed followed by `"entities"` (e.g., `TShirt: 42 entities`), and below it a breakdown line showing per-size counts.

- **FR-007**: The T-Shirt classifier MUST handle all Modified Fibonacci Story Point values (1, 2, 3, 5, 8, 13, 20, 40, 100) by mapping each to exactly one T-shirt size.

- **FR-008**: Entities with Story Point values not matching any mapping range MUST be classified as `"UNKNOWN"` and flagged with an appropriate warning.

- **FR-009**: Entities with missing or invalid Story Point values MUST be skipped with a `"MISSING_SP_VALUE"` warning and MUST NOT be counted in the total.

- **FR-010**: A dedicated RFC document MUST be created in `docs/rfcs/` documenting the T-Shirt Sizing methodology, mapping table, output formats (measure.json, metrics.json, CLI), and guidance for cross-specification comparison and Kanban sizing.

- **FR-011**: The mapping table MUST remain configurable — users can provide a custom mapping that overrides the default, following the same structural format.

### Key Entities

- **T-Shirt Size**: Defines a mapping entry with a label (XS, S, M, L, XL, XXL), a Story Point range (min, max), and an ordinal position. The six default entries form the complete mapping table.

- **Classified Work Item**: Represents a single entity after T-shirt classification. Contains the entity identifier, name, original Story Point value, assigned T-shirt size label, the mapping rule that produced the classification, and evidence references.

- **T-Shirt Measurement Result**: Aggregated result for a specification. Contains the run identifier, total entity count, list of classified work items, distribution histogram (count per size), source Story Points run ID, execution metadata, and any warnings.

- **T-Shirt Breakdown**: Per-size count entry used in `measure.json`. Contains a T-shirt size label as key and a `count` field with the integer number of entities in that size.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A specification with entities spanning all 9 Modified Fibonacci values produces exactly 6 size categories in the output distribution, with each entity classified into exactly one category.

- **SC-002**: Running a full pipeline on a specification with 10+ Story Point-classified entities produces a `measure.json` T-Shirt entry where `total` equals the entity count and is greater than 0.

- **SC-003**: The `measure.json` breakdown sums to the total (sum of all `count` values equals `total`).

- **SC-004**: The `metrics.json` T-Shirt entry contains an `entities` array where each element has all six required fields (`id`, `name`, `type`, `story_point_value`, `tshirt_size`, `mapping_rule`).

- **SC-005**: The CLI output shows `TShirt: N entities` where N is the actual number of entities classified, followed by a per-size breakdown line.

- **SC-006**: An entity with Story Point value 8 is classified as `"L"` (corrected from the previous mapping where it was `"M"`).

- **SC-007**: An entity with Story Point value 40 is classified as `"XL"` (corrected from the previous mapping where it was `"XXL"`).

- **SC-008**: The T-Shirt RFC document is created in `docs/rfcs/` and contains methodology, mapping table, output format specifications, and Kanban guidance.

## Assumptions

- The Story Points measurement engine is available and produces normalized Fibonacci values (1, 2, 3, 5, 8, 13, 20, 40, 100) for each entity in the pipeline context.
- The T-Shirt Sizing plugin continues to execute after Story Points in the pipeline, consuming its results via the `TSHIRT_CLASSIFICATION_COMPLETED` event.
- The `measure.json` and `metrics.json` output pipelines are already in place and the T-Shirt plugin integrates with them through standard payload keys.
- The mapping is a discrete lookup table — each Story Point value maps to exactly one T-shirt size. There is no fuzzy or weighted classification.
- The total in both `measure.json` and `metrics.json` represents the count of entities analyzed (not a sum of Story Points or any derived score).
- Specification decomposition into equal-effort items is a manual Kanban practice. SpecMetrics provides the T-Shirt distribution data; users apply their own process to chunk specifications.
- The existing T-Shirt plugin structure (classifier, models, handler, plugin) is preserved. Modifications are limited to mapping values, payload keys, and output integration.
