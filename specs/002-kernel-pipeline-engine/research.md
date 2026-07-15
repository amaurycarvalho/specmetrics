# Research: Kernel & Pipeline Engine

## Pipeline Engine Pattern

**Decision**: In-process event-driven pipeline with synchronous Event Bus.

**Rationale**: The Foundation doc defines an event-driven architecture where
each stage publishes immutable domain events and subscribed components execute
the next processing step. This decouples stages while preserving deterministic
execution order. An in-process synchronous bus avoids external dependencies and
simplifies the MVP.

**Alternatives considered**:
- Direct sequential invocation (simpler but violates plugin isolation)
- Async message queue (over-engineered for local-only MVP)
- External message broker (violates local-first constraint)

## Event Schema Design

**Decision**: Typed event classes using inheritance — base `PipelineEvent` with
dedicated subtypes per event type. Each event carries a `PipelineContext`
snapshot.

**Rationale**: Typed events enable static validation, clear handler signatures,
and straightforward serialization for debugging. Pydantic models align with the
constitution's technology stack.

**Alternatives considered**:
- Plain dicts (no type safety, harder to evolve schemas)
- Protobuf (over-engineered for in-process MVP)

## Handler Registration

**Decision**: Dictionary-based registry mapping event type → handler function,
populated at startup by Plugin Discovery.

**Rationale**: Simple, testable, easy to inspect. Handlers are stateless
functions that receive an event and return the next Pipeline Context version.

**Alternatives considered**:
- Decorator-based registration (more ergonomic but adds import-time coupling)
- Abstract base classes (adds inheritance overhead with no benefit for MVP)

## Concurrency Model

**Decision**: Single-threaded per execution; each pipeline run has an isolated
`PipelineContext`. Concurrent runs are independent.

**Rationale**: The Event Bus is synchronous and in-process. Thread safety is not
required because each execution owns its context. The Application Layer (CLI/MCP)
handles serialization of requests.

**Alternatives considered**:
- Thread pool (unnecessary complexity for local-first MVP)
- Async/await (adds cognitive overhead; can be introduced later if needed)

## Failure Handling

**Decision**: Fail-fast — any stage error halts the pipeline immediately. No
automatic retry at the pipeline level. The error event carries the originating
stage name and exception details.

**Rationale**: Matches SI-07 (Fail Fast) invariant. Partial results are dangerous
for functional measurement. Retry logic belongs to individual stages.

**Alternatives considered**:
- Retry with backoff (adds complexity; better suited for publisher plugins)
- Compensating transactions (over-engineered; stages are stateless readers)
