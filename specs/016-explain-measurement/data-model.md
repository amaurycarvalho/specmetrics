# Data Model: Explain Measurement

## Entities

### MeasurementExplanation

The top-level explanation for a completed measurement run.

| Field | Type | Description |
|---|---|---|
| `run_id` | str | Unique identifier for the measurement run |
| `spec_path` | str | Path to the specification document that was measured |
| `measured_at` | datetime | Timestamp when measurement was performed |
| `metrics` | list[MetricExplanation] | Per-metric explanations |
| `applied_rules` | list[AppliedRule] | All Rule Pack rules applied during measurement |
| `summary` | ExplanationSummary | Aggregate counts and metadata |

**Relationships**: Produced by ExplainService. Contains one MetricExplanation per metric, zero or more AppliedRule records.

### MetricExplanation

Explanation for a single metric value (e.g., "Functional Size = 12").

| Field | Type | Description |
|---|---|---|
| `metric_name` | str | Name of the metric (e.g., "functional_size", "function_count") |
| `metric_value` | int \| float | The numerical result |
| `elements` | list[ElementContribution] | Individual specification elements that contributed to this metric |
| `applied_rules` | list[AppliedRule] | Rules that specifically affected this metric |
| `computation_summary` | str | Brief human-readable description of how the value was derived |

**Relationships**: Belongs to a MeasurementExplanation. Contains ElementContribution records for each counted element.

### ElementContribution

A single specification element that contributed to a metric.

| Field | Type | Description |
|---|---|---|
| `element_id` | str | Unique identifier for the element in the CFM |
| `element_type` | str | Type of element (e.g., "ILF", "EIF", "EI", "EO", "EQ", "entity", "operation") |
| `element_label` | str | Human-readable name or label of the element |
| `complexity` | str \| None | Complexity rating ("Low", "Average", "High") or None if not applicable |
| `weight` | int \| None | Functional weight assigned to this element |
| `evidence` | list[EvidenceReference] | Source specification text fragments that justify this element's existence |
| `applied_rules` | list[AppliedRule] | Rules that modified this element's classification, weight, or inclusion |

**Relationships**: Belongs to a MetricExplanation. Contains EvidenceReference records for traceability.

### EvidenceReference

A pointer to the specific specification section and text that justifies a counted element.

| Field | Type | Description |
|---|---|---|
| `document_id` | str | Identifier of the source specification document |
| `section_id` | str \| None | Section heading or path within the document |
| `text` | str | The specific text fragment that supports the element |
| `node_id` | str | ID of the corresponding node in the Evidence Graph |
| `confidence` | float \| None | Extraction confidence score (0.0–1.0) |

**Relationships**: Belongs to an ElementContribution. References a node in the Evidence Graph.

### AppliedRule

A record of a Rule Pack rule that was applied during measurement.

| Field | Type | Description |
|---|---|---|
| `rule_pack_id` | str | Identifier of the Rule Pack containing this rule |
| `rule_id` | str | Unique rule identifier within the Rule Pack |
| `rule_type` | str | Type of rule (e.g., "exclusion", "complexity_override", "weight_override", "vaf") |
| `description` | str | Human-readable description of what the rule does |
| `effect` | str | Description of how this rule affected the measurement (e.g., "Excluded element E002", "Overrode complexity to High") |

**Relationships**: Referenced by MeasurementExplanation (all-applied) and MetricExplanation/ElementContribution (metric-specific).

### ExplanationComparison

A comparison between two MeasurementExplanation instances.

| Field | Type | Description |
|---|---|---|
| `baseline_run_id` | str | Run ID of the earlier/baseline measurement |
| `comparison_run_id` | str | Run ID of the later measurement |
| `changed_metrics` | list[MetricChange] | Metrics whose values differ between runs |
| `added_metrics` | list[str] | Metric names present in comparison but not in baseline |
| `removed_metrics` | list[str] | Metric names present in baseline but not in comparison |
| `unchanged_metrics` | list[str] | Metric names with identical values in both runs |
| `summary` | str | Human-readable summary of differences |

### MetricChange

A metric whose value changed between two measurement runs.

| Field | Type | Description |
|---|---|---|
| `metric_name` | str | Name of the metric that changed |
| `baseline_value` | int \| float | Value in the baseline measurement |
| `comparison_value` | int \| float | Value in the comparison measurement |
| `delta` | int \| float | Difference (comparison - baseline) |
| `changed_elements` | list[ElementChange] | Individual elements that were added, removed, or modified |

### ElementChange

An element-level change between two measurement runs.

| Field | Type | Description |
|---|---|---|
| `element_id` | str | Identifier of the changed element |
| `change_type` | str | "added", "removed", "complexity_changed", "weight_changed" |
| `baseline_state` | dict | Element attributes in the baseline (empty if added) |
| `comparison_state` | dict | Element attributes in the comparison (empty if removed) |

### ExplanationSummary

Aggregate metadata for an explanation.

| Field | Type | Description |
|---|---|---|
| `total_metrics` | int | Number of metrics in the explanation |
| `total_elements` | int | Total elements across all metrics |
| `total_evidence_refs` | int | Total evidence references |
| `total_rules_applied` | int | Number of unique rules applied |
| `generated_at` | datetime | When the explanation was produced |

## State Transitions

```text
Measurement Result (from Measurement Engine)
        │
        ▼
ExplainService.explain(run_id, metric_name?)
        │
        ├──► Load CFM elements for given run
        ├──► Load Evidence Graph for given run
        ├──► Load AppliedRule records for given run
        │
        ├──► For each requested metric:
        │       ├──► Identify contributing CFM elements
        │       ├──► Trace each element to evidence (Evidence Graph)
        │       ├──► Attach applicable rules
        │       └──► → MetricExplanation
        │
        └──► Aggregate → MeasurementExplanation
```

Comparison flow:

```text
ExplainService.compare(baseline_run_id, comparison_run_id)
        │
        ├──► Load MeasurementExplanation for baseline
        ├──► Load MeasurementExplanation for comparison
        │
        ├──► Align metrics by name
        ├──► For each metric:
        │       ├──► Compare values
        │       ├──► Diff elements by element_id
        │       └───► → MetricChange
        │
        └──► Aggregate → ExplanationComparison
```

## Validation Rules

| Rule | Description |
|---|---|
| `evidence-traceable` | Every element in a MetricExplanation must have at least one EvidenceReference |
| `metric-value-matches-sum` | Sum of element weights must equal the reported metric value |
| `comparison-ids-match` | Comparison runs must reference existing measurement run IDs |
