# Measurement API Contract: Business Complexity Points (BCP)

## Plugin Interface

```python
class MeasurementPlugin(Protocol):
    def plugin_id(self) -> str: ...
    def supported_methodology(self) -> str: ...
    def supported_component_types(self) -> list[str]: ...
    def measure(
        self,
        cfm: CanonicalFunctionalModel,
        provider: str | None = None,
    ) -> BCPMeasurementResult: ...
```

## Handler Interface

```python
class BCPHandler:
    @property
    def handled_event_type(self) -> EventType: ...       # MEASUREMENT_COMPLETED
    @property
    def handler_id(self) -> str: ...                     # "bcp_measurement"
    @property
    def stage_name(self) -> str: ...                     # "BCP Measurement"
    def handle(self, event: PipelineEvent) -> PipelineContext: ...
```

## Event Contract

Handler stores payload in `ctx.with_stage_output("measurement_result", payload)`:

```json
{
  "method": "BCP",
  "sdk_version": "1.0.0",
  "provider": "openai",
  "total_bcp": 47.5,
  "measured_items": 3,
  "items_succeeded": 3,
  "items_failed": 0,
  "duration_ms": 2450,
  "warnings": []
}
```

## Output JSON Format

```json
{
  "method": "BCP",
  "sdk_version": "1.0.0",
  "provider": "openai",
  "total_bcp": 47.5,
  "items": [
    {
      "element_id": "fp-001",
      "element_name": "Process Order",
      "generated_story": "# User Story: Process Order\n\nAs a customer...",
      "sdk_response": {"total_bcp": 18.0, "breakdown": {"business_logic": 8.0}},
      "bcp_score": 18.0,
      "component_breakdown": {"business_logic": 8.0},
      "status": "success",
      "evidence_refs": [{"element_id": "fp-001", "document_id": "spec.md"}]
    }
  ],
  "execution_metadata": {
    "duration_ms": 2450, "total_fps_processed": 3,
    "items_succeeded": 3, "items_failed": 0,
    "sdk_call_count": 3, "sdk_errors": 0
  },
  "warnings": []
}
```

## Adapter Protocol

```python
class BcpSdkAdapter(Protocol):
    def calculate(self, story_content: str) -> dict[str, Any]: ...
    def batch_calculate(self, stories: list[str]) -> list[dict[str, Any]]: ...
```

## Test Double

```python
class FakeBcpSdkAdapter:
    def calculate(self, story_content: str) -> dict[str, Any]:
        return {
            "total_bcp": 15.0,
            "breakdown": {"business_logic": 8.0, "data": 4.0, "integration": 3.0},
        }
```
