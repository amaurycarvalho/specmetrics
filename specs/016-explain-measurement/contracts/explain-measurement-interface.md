# Explain Measurement Contracts

## CLI Interface

### Command: `specmetrics explain`

```
Usage: specmetrics explain [OPTIONS] RUN_ID

Arguments:
  RUN_ID  Identifier of the measurement run to explain  [required]

Options:
  --metric TEXT         Specific metric to explain (e.g., "functional_size");
                        omit to explain all metrics
  --format TEXT         Output format: text (default), json
  --compare TEXT        Compare with another run ID (e.g., --compare <run_id>)
  --help                Show this message and exit
```

**Exit codes**:
- `0` — Explanation generated successfully
- `1` — Run ID not found or explanation failed
- `2` — Invalid arguments

### JSON Output Format

When `--format json` is specified, output is written to stdout as JSON:

```json
{
  "run_id": "meas-20260716-143022",
  "spec_path": "specs/015-validation-pipeline/spec.md",
  "measured_at": "2026-07-16T14:30:22Z",
  "metrics": [
    {
      "metric_name": "functional_size",
      "metric_value": 12,
      "computation_summary": "Sum of weighted functions: 3 ILF (9) + 2 EIF (3) = 12",
      "elements": [
        {
          "element_id": "func-001",
          "element_type": "ILF",
          "element_label": "UserRepository",
          "complexity": "Low",
          "weight": 3,
          "evidence": [
            {
              "document_id": "specs/015-validation-pipeline/spec.md",
              "section_id": "User Scenarios & Testing",
              "text": "System MUST accept a specification document as input",
              "node_id": "ev-001",
              "confidence": 0.95
            }
          ],
          "applied_rules": []
        }
      ],
      "applied_rules": []
    }
  ],
  "applied_rules": [],
  "summary": {
    "total_metrics": 1,
    "total_elements": 1,
    "total_evidence_refs": 1,
    "total_rules_applied": 0,
    "generated_at": "2026-07-16T14:31:05Z"
  }
}
```

### Comparison Output

When `--compare` is specified, output includes a comparison section:

```json
{
  "run_id": "meas-20260716-143022",
  "comparison": {
    "baseline_run_id": "meas-20260715-120000",
    "comparison_run_id": "meas-20260716-143022",
    "changed_metrics": [
      {
        "metric_name": "functional_size",
        "baseline_value": 10,
        "comparison_value": 12,
        "delta": 2,
        "changed_elements": [
          {
            "element_id": "func-002",
            "change_type": "added",
            "baseline_state": {},
            "comparison_state": {
              "element_type": "ILF",
              "complexity": "Low",
              "weight": 3
            }
          }
        ]
      }
    ],
    "added_metrics": [],
    "removed_metrics": ["obsolete_metric"],
    "unchanged_metrics": ["function_count"],
    "summary": "1 metric changed, 0 added, 1 removed, 1 unchanged"
  },
  ...
}
```

## Python API

### ExplainService

```python
class ExplainService:
    def explain(
        self,
        run_id: str,
        metric_name: str | None = None,
    ) -> MeasurementExplanation: ...

    def compare(
        self,
        baseline_run_id: str,
        comparison_run_id: str,
    ) -> ExplanationComparison: ...

    def load_explanation(self, run_id: str) -> MeasurementExplanation: ...
```

### Formatter Protocol (Plugin Interface)

```python
class ExplanationFormatter(Protocol):
    name: str

    def format(self, explanation: MeasurementExplanation) -> str: ...
    def format_comparison(self, comparison: ExplanationComparison) -> str: ...
```

Entry point group: `specmetrics.explanation_formatters`

### EvidenceTracer

```python
class EvidenceTracer:
    def __init__(self, graph: EvidenceGraph): ...

    def trace_element(
        self,
        element_id: str,
        max_depth: int = 3,
    ) -> list[EvidenceReference]: ...

    def trace_metric(
        self,
        element_ids: list[str],
    ) -> dict[str, list[EvidenceReference]]: ...
```

## Data Sources

| Source | Access Method | Purpose |
|---|---|---|
| Evidence Graph | `EvidenceGraph.nodes`, `GraphBackend.traverse()` | Evidence traceability |
| CFM Elements | `CFM.get_elements()`, `CFM.get_metrics()` | Identified elements and their classifications |
| Applied Rules | Rule Pack application records | Rule effects on metrics |
| Measurement Results | Measurement engine output | Metric values and their composition |

## Configuration

### Explanation Settings

```yaml
# .specify/explanation.yml
explanation:
  max_evidence_depth: 3
  include_low_confidence: false
  min_confidence: 0.5
  default_format: text
  formatters:
    - id: text
      enabled: true
    - id: json
      enabled: true
```
