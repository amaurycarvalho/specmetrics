# Measurement API Contract: Token Points

## Plugin Interface

The Token Points plugin exposes a `MeasurementPlugin` protocol consistent with SFP/FPA/SNAP:

```python
class MeasurementPlugin(Protocol):
    def plugin_id(self) -> str: ...
    def supported_methodology(self) -> str: ...
    def supported_component_types(self) -> list[str]: ...
    def measure(
        self,
        cfm: CanonicalFunctionalModel,
        csm: CanonicalSpecificationModel | None = None,
        calibration: CalibrationProfile | None = None,
    ) -> TokenPointsMeasurement: ...
```

## Handler Interface

```python
class TokenPointsHandler:
    @property
    def handled_event_type(self) -> EventType: ...           # MEASUREMENT_COMPLETED
    @property
    def handler_id(self) -> str: ...                         # "token_points_measurement"
    @property
    def stage_name(self) -> str: ...                         # "Token Points Measurement"
    def handle(self, event: PipelineEvent) -> PipelineContext: ...
```

## Event Contract

The handler stores a dict payload in `ctx.with_stage_output("measurement_result", payload)`:

```json
{
  "total_score": 47.5,
  "specification_cost": 18.5,
  "code_generation_cost": 29.0,
  "element_counts": {
    "csm": 12,
    "cfm": 8,
    "total": 20
  },
  "calibration_version": "1.0",
  "top_contributors": [
    {"type": "functional_process", "count": 3, "total": 15.0},
    {"type": "decision", "count": 4, "total": 6.0}
  ],
  "duration_ms": 1.2,
  "warnings": []
}
```

## Calibration File Format

Calibration profiles are YAML files placed in `.specmetrics/calibration/`:

```yaml
# .specmetrics/calibration/token-points.yml
version: "1.0"
specification_cost:
  activities:
    exploration: 2.0
    clarification: 3.0
    refinement: 2.5
    review: 1.5
    validation: 2.0
  decisions: 1.5
  assumptions: 1.0
  constraints: 1.5
  risks: 2.0
  open_questions: 1.0
  acceptance_criteria: 1.0
  glossary_terms: 0.5

code_generation_cost:
  functional_processes: 5.0
  business_rules: 3.0
  operations: 2.0
  data_groups: 2.0
  relationships: 1.0
  actors: 1.0
```

## Test Double

```python
class FakeTokenPointsPlugin:
    def plugin_id(self) -> str:
        return "token_points"

    def measure(self, cfm, csm=None, calibration=None):
        return TokenPointsMeasurement(
            run_id="test-run",
            total_score=10.0,
            specification_cost=SpecificationCost(total=4.0, contributions=[]),
            code_generation_cost=CodeGenerationCost(total=6.0, contributions=[]),
            calibration_version="1.0",
            measurement_metadata=MeasurementMetadata(total_elements_processed=5),
        )
```
