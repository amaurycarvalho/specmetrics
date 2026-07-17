# Measurement API Contract: Cognitive Points

## Plugin Interface

```python
class MeasurementPlugin(Protocol):
    def plugin_id(self) -> str: ...
    def supported_methodology(self) -> str: ...
    def supported_component_types(self) -> list[str]: ...
    def measure(
        self,
        cfm: CanonicalFunctionalModel,
        csm: CanonicalSpecificationModel | None = None,
        calibration: CognitiveCalibrationProfile | None = None,
    ) -> CognitivePointsMeasurement: ...
```

## Handler Interface

```python
class CognitivePointsHandler:
    @property
    def handled_event_type(self) -> EventType: ...           # MEASUREMENT_COMPLETED
    @property
    def handler_id(self) -> str: ...                         # "cognitive_points_measurement"
    @property
    def stage_name(self) -> str: ...                         # "Cognitive Points Measurement"
    def handle(self, event: PipelineEvent) -> PipelineContext: ...
```

## Event Contract

Handler stores payload in `ctx.with_stage_output("measurement_result", payload)`:

```json
{
  "total_cognitive_points": 13,
  "raw_score": 42.5,
  "specification_review_effort": { "total_raw": 18.5, "bloom_breakdown": {"analyze": 5, "evaluate": 3} },
  "functional_validation_effort": { "total_raw": 24.0, "bloom_breakdown": {"create": 2, "apply": 4} },
  "fibonacci_normalization": { "raw_score": 42.5, "threshold": 35, "output": 13 },
  "element_counts": { "csm": 8, "cfm": 6, "total": 14 },
  "bloom_distribution": { "remember": 1, "understand": 3, "apply": 4, "analyze": 5, "evaluate": 3, "create": 2 },
  "calibration_version": "1.0",
  "duration_ms": 0.8,
  "warnings": []
}
```

## Calibration YAML Format

```yaml
# .specmetrics/calibration/cognitive-points.yml
version: "1.0"
bloom_levels:
  remember: 1.0
  understand: 2.0
  apply: 3.0
  analyze: 4.0
  evaluate: 5.0
  create: 8.0

bloom_mappings:
  exploration: "understand"
  clarification: "analyze"
  refinement: "apply"
  review: "evaluate"
  validation: "evaluate"
  decision: "evaluate"
  assumption: "understand"
  constraint: "apply"
  risk: "analyze"
  open_question: "analyze"
  acceptance_criterion: "apply"
  glossary_term: "remember"
  functional_process: "create"
  business_rule: "apply"
  operation: "apply"
  data_group: "understand"
  relationship: "understand"
  actor: "remember"

default_bloom_level: "analyze"

fibonacci_normalization:
  thresholds: [5, 12, 22, 35, 55, 85, 130]
  output_values: [1, 3, 5, 8, 13, 20, 40, 100]
```

## Test Double

```python
class FakeCognitivePointsPlugin:
    def plugin_id(self) -> str:
        return "cognitive_points"

    def measure(self, cfm, csm=None, calibration=None):
        return CognitivePointsMeasurement(
            run_id="test-run",
            total_cognitive_points=8,
            raw_score=25.0,
            specification_review_effort=SpecificationReviewEffort(total_raw=10.0, contributions=[]),
            functional_validation_effort=FunctionalValidationEffort(total_raw=15.0, contributions=[]),
            fibonacci_normalization=FibonacciNormalizationResult(raw_score=25.0, threshold_applied=22, output_value=8),
            calibration_version="1.0",
            measurement_metadata=MeasurementMetadata(total_elements_processed=6),
        )
```
