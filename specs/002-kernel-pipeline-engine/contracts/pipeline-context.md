# Pipeline Context Contract

## Interface

```python
@dataclass(frozen=True)
class PipelineContext:
    """
    Immutable container for all pipeline execution state.

    A new instance is created for each event publication. The previous version
    is preserved in the event log.
    """
    execution_id: UUID

    # Stage outputs (None until produced)
    repository: Repository | None = None
    adapter_result: AdapterResult | None = None
    evidence_graph: EvidenceGraph | None = None
    canonical_model: CanonicalModel | None = None
    measurement_result: MeasurementResult | None = None
    exported_files: list[FilePath] | None = None

    # Execution tracking
    published_events: tuple[PipelineEvent, ...] = ()
    diagnostics: Diagnostics | None = None
    metadata: ExecutionMetadata | None = None
```

## Design Rules

1. **Immutability**: All fields are frozen. To update, construct a new instance
   via `dataclasses.replace()` or a builder method.
2. **Optional fields**: Stage outputs are `None` until their producing stage
   completes. Downstream handlers MUST check for `None` on their inputs.
3. **Event log**: `published_events` is a tuple (immutable sequence) — events
   are appended by constructing a new context with `published_events + (event,)`.
4. **No shared references**: Each context version owns its data. Previous
   versions remain intact in the event log for audit.
5. **Builder method**:

   ```python
   def with_stage_output(self, event_type: EventType, payload: Any) -> PipelineContext:
       """Return a new context with the stage output populated and event logged."""
   ```
