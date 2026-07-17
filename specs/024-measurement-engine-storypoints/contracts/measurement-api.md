# Measurement API Contract: Story Points

## Plugin Interface

```python
class MeasurementPlugin(Protocol):
    def plugin_id(self) -> str: ...
    def supported_methodology(self) -> str: ...
    def supported_component_types(self) -> list[str]: ...
    def measure(
        self,
        cfm: CanonicalFunctionalModel,
        previous_fingerprints: dict[str, str] | None = None,
    ) -> StoryPointMeasurementResult: ...
```

## Handler Interface

```python
class StoryPointsHandler:
    @property
    def handled_event_type(self) -> EventType: ...           # MEASUREMENT_COMPLETED
    @property
    def handler_id(self) -> str: ...                         # "storypoints_measurement"
    @property
    def stage_name(self) -> str: ...                         # "Story Points Measurement"
    def handle(self, event: PipelineEvent) -> PipelineContext: ...
```

## Event Contract

Handler stores payload in `ctx.with_stage_output("measurement_result", payload)`:

```json
{
  "method": "StoryPoints",
  "scale": "ModifiedFibonacci",
  "total_story_points": 196,
  "estimated_items": 37,
  "distribution": {"3": 8, "5": 12, "8": 10, "13": 5, "20": 2},
  "applied_rule_pack": "default",
  "duration_ms": 45,
  "warnings": []
}
```

## Output JSON Format

```json
{
  "method": "StoryPoints",
  "scale": "ModifiedFibonacci",
  "total_story_points": 196,
  "items": [
    {
      "element_id": "fp-001",
      "element_name": "Process Order",
      "raw_score": 14.5,
      "normalized_value": 8,
      "factor_breakdown": {
        "business_interactions": 3.0,
        "logical_information": 4.0,
        "business_rule_density": 4.5,
        "workflow_breadth": 3.0
      },
      "applied_rules": ["default_coefficients_v1"],
      "evidence_refs": [
        {"graph_node_id": "node-01", "document_id": "spec.md", "text": "System shall process orders"}
      ]
    }
  ],
  "distribution": {"3": 8, "5": 12, "8": 10, "13": 5, "20": 2},
  "applied_rule_pack": "default",
  "execution_metadata": {
    "duration_ms": 45,
    "total_fps_processed": 37,
    "fps_estimated": 37,
    "fps_merged_as_duplicates": 0,
    "version": "1.0"
  },
  "warnings": []
}
```

## Test Double

```python
class FakeStoryPointsPlugin:
    def plugin_id(self) -> str:
        return "storypoints"

    def measure(self, cfm, previous_fingerprints=None):
        return StoryPointMeasurementResult(
            run_id="test-run",
            total_story_points=196,
            items=[
                FunctionalWorkItem(
                    element_id="fp-001", element_name="Process Order",
                    raw_score=14.5, normalized_value=8,
                    factor_breakdown={"business_interactions": 3.0},
                )
            ],
            distribution={8: 1},
            execution_metadata=ExecutionMetadata(duration_ms=45, total_fps_processed=1, fps_estimated=1),
        )
```
