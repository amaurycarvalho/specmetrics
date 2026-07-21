# Feature Specification: Cognitive Points Breakdown

**Feature Branch**: `042-cognitive-points-breakdown`

**Created**: 2026-07-21

**Status**: Draft

**Input**: User description: "Implemente para o Cognitive Points: 1. Adicione a tag 'breakdown' no measure.json para exibir o total de score aberto por bloom_level. 2. Exiba na tela abaixo de 'Cognitive Points' em 'Results' o total aberto por bloom_level."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bloom-Level Score Breakdown in measure.json (Priority: P1)

As a user consuming the measure.json output programmatically, I want the Cognitive Points entry to include a breakdown of the total raw score by Bloom taxonomy level (remember, understand, apply, analyze, evaluate, create), so I can understand which cognitive levels contribute most to the overall score without having to process the full entity list.

**Why this priority**: The measure.json is the primary machine-readable output of a measurement run. Exposing the score breakdown by Bloom level enables downstream tools, dashboards, and scripts to analyze the cognitive profile of specifications without parsing the detailed entity-level data.

**Independent Test**: Run `specmetrics measure` on any project and inspect `measure.json`. Verify the Cognitive Points entry contains a `breakdown` object with one key per Bloom level found, each containing a `total` field with the sum of partial scores for all elements at that level.

**Acceptance Scenarios**:

1. **Given** a measurement run that processes both CSM and CFM elements with varying Bloom classifications, **When** `measure.json` is generated, **Then** the Cognitive Points entry includes a `breakdown` field containing `{ "understand": { "total": X }, "apply": { "total": Y }, ... }` where each total is the sum of `partial_score` for all elements at that Bloom level.

2. **Given** the raw score total of 44474.5 with breakdown totals 890 (understand), 1500 (apply), etc., **When** all breakdown totals are summed, **Then** the sum equals the Cognitive Points raw score total (allowing for minor floating-point rounding).

3. **Given** a measurement with all elements classified at a single Bloom level, **When** `measure.json` is generated, **Then** the breakdown contains only that one level with its total.

---

### User Story 2 - Bloom-Level Score Breakdown in CLI Display (Priority: P1)

As a user running `specmetrics measure` from the terminal, I want to see the Cognitive Points total score broken down by Bloom taxonomy level directly below the "Cognitive Points" line in the Results section, so I can immediately understand the cognitive profile of the measured specification without inspecting external files.

**Why this priority**: The CLI is the primary user interface. Displaying the Bloom-level breakdown alongside the total score provides immediate insight into the cognitive effort distribution, which is essential for comparing specifications and making Kanban sizing decisions.

**Independent Test**: Run `specmetrics measure` on any project. Verify that below the "Cognitive Points" line, indented lines appear showing each Bloom level present and its total score (e.g., `Understand: 444`).

**Acceptance Scenarios**:

1. **Given** a measurement run with elements classified across multiple Bloom levels, **When** the text output is displayed, **Then** below `Cognitive Points: {total}`, indented lines show each Bloom level with its total score in the format `    {Level}: {total}`.

2. **Given** a measurement where all elements fall into three Bloom levels (understand, apply, create), **When** the text output is displayed, **Then** exactly three indented lines appear below Cognitive Points, each showing the corresponding level name (capitalized) and total score.

3. **Given** the breakdown totals sum to the raw score, **When** the user inspects the CLI output, **Then** the sum of the displayed breakdown values (rounded to a reasonable precision) matches the displayed Cognitive Points total.

---

### Edge Cases

- **Empty specification (no elements)**: The breakdown object in measure.json is an empty dict `{}`. The CLI displays no indented breakdown lines below the total (only the total line with value 0 is shown).
- **Elements from only one Bloom level**: The breakdown contains a single entry. The CLI displays one indented line. The breakdown total equals the Cognitive Points total.
- **Bloom level with zero elements but present in the distribution key set**: The level is excluded from the breakdown (only levels with non-zero total appear). This prevents displaying levels with `total: 0`.
- **Very large score totals**: Floating-point precision is sufficient for score values (Python float). No explicit rounding is applied to the breakdown values; consumers may round as needed for display.
- **JSON output mode (`--format json`)**: The JSON output already includes the full payload. The breakdown added to measure.json is sufficient; no separate JSON output change is needed since `metrics.json` and `measure.json` already serve as the structured output.

## Constitution Check *(mandatory)*

**Engaged Principles**:

- **VI - Explainability by Design**: The Bloom-level breakdown makes the Cognitive Points measurement more explainable by showing how much each cognitive level contributes to the total score. Users can now see at a glance whether a specification is heavy in "understand" (comprehension tasks) vs "create" (generative tasks).
- **VII - Canonical Representation**: The breakdown operates on the same CognitiveContribution entities already produced by the measurement engine. No changes to the CSM, CFM, or Bloom classification logic are required.
- **VIII - Plugin-Oriented Architecture**: The score aggregation by Bloom level is computed within the Cognitive Points plugin and exposed as a new payload key. The orchestrator and CLI consume this key without modifying the plugin interface.
- **XI - Observability as a Native Capability**: The breakdown enriches the structured measurement output (measure.json) with more granular data, improving the platform's observability of cognitive effort distribution.
- **XIII - Evolution Without Disruption**: The new `breakdown` field is additive — existing consumers of measure.json ignore unknown keys. The CLI display adds new lines but preserves the existing total display format.

**Compliance Notes**: This feature is purely additive. It computes a new summary aggregation from existing data (sum of partial_score per bloom_level across all CognitiveContribution entities) and exposes it in two places: the machine-readable measure.json and the human-readable CLI output. No changes to measurement formulas, Bloom classification, or calibration are required.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Cognitive Points measurement plugin MUST compute a Bloom-level score breakdown — the sum of `partial_score` (Bloom weight + content score) for all CognitiveContribution entities at each Bloom taxonomy level — and expose it via a new payload key `cognitive_bloom_breakdown`.
- **FR-002**: The `cognitive_bloom_breakdown` payload value MUST be a mapping of `{bloom_level: total_score}` where `bloom_level` is a string (one of: remember, understand, apply, analyze, evaluate, create) and `total_score` is a float representing the sum of partial scores for all elements classified at that level.
- **FR-003**: The measure.json builder in the orchestrator MUST map the `cognitive_bloom_breakdown` payload key to a `breakdown` field in the Cognitive Points entry of the measure stage output.
- **FR-004**: The CLI text formatter MUST display the Bloom-level score breakdown below the Cognitive Points total line, using indented lines in the format `    {Level}: {total}` where Level is the capitalized bloom level name and total is the score value.
- **FR-005**: The breakdown values in both measure.json and CLI MUST sum to the Cognitive Points total raw score (allowing for minor floating-point differences).
- **FR-006**: Bloom levels with zero total score (no elements at that level) MUST be excluded from both the measure.json breakdown and the CLI display.
- **FR-007**: The existing payload keys, data models, and calibration profiles MUST remain unchanged — the bloom breakdown is a new payload key that does not modify existing structures.

### Key Entities

- **BloomBreakdown** (new payload entry): A `dict[str, float]` mapping Bloom taxonomy level names to total partial scores. Computed by aggregating `partial_score` across all `CognitiveContribution` entities grouped by `bloom_level`. Exposed as `cognitive_bloom_breakdown` in the measurement payload.
- **measure.json breakdown field** (updated): The Cognitive Points entry in the measure stage entities gains an optional `breakdown` field, a dict of `{bloom_level: {total: float}}`, populated from the `cognitive_bloom_breakdown` payload key.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After running `specmetrics measure` on any project with at least one specification element, `measure.json` contains a Cognitive Points entry whose `breakdown` field is a non-empty dict with per-bloom-level score totals.
- **SC-002**: The sum of all values in the `breakdown` field of `measure.json` equals the Cognitive Points `total` field (within 0.01 tolerance for floating-point arithmetic).
- **SC-003**: The CLI text output displays indented Bloom-level breakdown lines below the Cognitive Points total line, with each line showing a capitalized Bloom level name and its corresponding score.
- **SC-004**: Running Cognitive Points on an empty specification (no elements) produces a measure.json entry with `breakdown: {}` and no indented breakdown lines in the CLI.

## Assumptions

- The Cognitive Points plugin's `CognitiveContribution` list (already available as `cognitive_entities` in the payload) is the authoritative source for per-element Bloom classification and partial scores. The breakdown aggregation uses these contributions.
- The Bloom taxonomy has exactly 6 levels (remember, understand, apply, analyze, evaluate, create). The capitalization for display uses the English titles: Remember, Understand, Apply, Analyze, Evaluate, Create.
- The `measurement_result` dictionary in the pipeline context is the same dict built by `ctx.merge_stage_output("measurement_result", payload)` — new payload keys added in the plugin are automatically available in the orchestrator.
- No changes to the `MetricOutputItem` model are needed — the breakdown data is read from `measurement_result_raw` in the formatter (same pattern used by tshirt and function points breakdowns).
- The breakdown aggregation can be computed efficiently from the existing `all_cognitive_contributions` list in the plugin's `handle()` method without introducing a separate calculation pass.
