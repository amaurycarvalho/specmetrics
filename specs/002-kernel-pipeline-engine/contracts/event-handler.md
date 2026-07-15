# Event Handler Contract

## Interface

```python
class EventHandler(Protocol):
    """Contract for all pipeline stage handlers."""

    @property
    def handled_event_type(self) -> EventType:
        """The event type this handler subscribes to."""
        ...

    @property
    def handler_id(self) -> str:
        """Unique identifier (e.g. 'adapter.openspec')."""
        ...

    @property
    def stage_name(self) -> str:
        """Human-readable stage name for diagnostics."""
        ...

    def handle(self, event: PipelineEvent) -> PipelineContext:
        """
        Process an event and return the next Pipeline Context version.

        Args:
            event: The immutable event published by the previous stage.

        Returns:
            A new PipelineContext with the stage's output populated.

        Raises:
            StageError: If the stage cannot complete successfully.
              The pipeline will halt and report this error.
        """
        ...
```

## Contract Rules

1. `handle()` MUST be a pure function — given the same event + context, it MUST
   produce the same output (determinism).
2. `handle()` MUST NOT mutate the received event or context — it returns a
   **new** context instance.
3. `handle()` MUST complete synchronously. Async stages are not supported in
   Release 0.1.
4. On failure, `handle()` MUST raise `StageError` with a descriptive message and
   the stage name. The Pipeline Engine catches this and publishes
   `PIPELINE_FAILED`.

## Registration

Handlers are registered at startup via the Handler Registry:

```python
registry = HandlerRegistry()
registry.register(MyAdapterHandler())  # registers for handler.handled_event_type
```

The registry is populated once and remains immutable during pipeline execution.
