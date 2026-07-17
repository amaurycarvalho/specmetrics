# Measurement API Contract: T-Shirt Sizing

## Plugin Interface

```python
class MeasurementPlugin(Protocol):
    def plugin_id(self) -> str: ...
    def supported_methodology(self) -> str: ...
    def supported_component_types(self) -> list[str]: ...
    def measure(
        self,
        story_points_result: StoryPointMeasurementResult,
        mapping_override: list[TShirtSize] | None = None,
    ) -> TShirtMeasurementResult: ...
```

## Handler Interface

```python
class TShirtHandler:
    @property
    def handled_event_type(self) -> EventType: ...       # TSHIRT_CLASSIFICATION_COMPLETED
    @property
    def handler_id(self) -> str: ...                     # "tshirt_measurement"
    @property
    def stage_name(self) -> str: ...                     # "T-Shirt Sizing"
    def handle(self, event: PipelineEvent) -> PipelineContext: ...
```

## Event Contract

Handler stores payload in `ctx.with_stage_output("measurement_result", payload)`:

```json
{
  "method": "TShirtSizing",
  "scale": "XS-S-M-L-XL-XXL",
  "total_items": 37,
  "distribution": {"XS": 3, "S": 8, "M": 14, "L": 7, "XL": 3, "XXL": 2},
  "applied_rule_pack": "default",
  "source_measurement_run_id": "run-abc-123",
  "duration_ms": 2.1,
  "warnings": []
}
```

## Output JSON Format

```json
{
  "method": "TShirtSizing",
  "scale": "XS-S-M-L-XL-XXL",
  "total_items": 37,
  "items": [
    {
      "element_id": "fp-001",
      "element_name": "Process Order",
      "story_point_value": 8,
      "tshirt_size": "M",
      "mapping_rule": "default: 5-8 → M",
      "evidence_refs": [
        {"element_id": "fp-001", "story_point_value": 8, "mapping_rule": "default: 5-8 → M"}
      ],
      "applied_rule_pack": "default"
    }
  ],
  "distribution": {"XS": 3, "S": 8, "M": 14, "L": 7, "XL": 3, "XXL": 2},
  "applied_rule_pack": "default",
  "source_measurement_run_id": "run-abc-123",
  "execution_metadata": {"duration_ms": 2.1, "total_fps_processed": 37, "version": "1.0"},
  "warnings": []
}
```

## Test Double

```python
class FakeTShirtPlugin:
    def plugin_id(self) -> str:
        return "tshirt"

    def measure(self, story_points_result, mapping_override=None):
        return TShirtMeasurementResult(
            run_id="test-run",
            total_items=3,
            items=[
                FunctionalWorkItem(element_id="fp-001", element_name="A", story_point_value=3, tshirt_size="S"),
                FunctionalWorkItem(element_id="fp-002", element_name="B", story_point_value=8, tshirt_size="M"),
                FunctionalWorkItem(element_id="fp-003", element_name="C", story_point_value=20, tshirt_size="XL"),
            ],
            distribution={"S": 1, "M": 1, "XL": 1},
            execution_metadata=ExecutionMetadata(duration_ms=1.0, total_fps_processed=3),
        )
```
