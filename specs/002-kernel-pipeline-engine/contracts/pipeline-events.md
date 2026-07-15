# Pipeline Events Catalog

## Event Type Enum

```python
class EventType(Enum):
    REPOSITORY_LOADED = "repository_loaded"
    DOCUMENTS_DISCOVERED = "documents_discovered"
    SEMANTIC_EXTRACTION_COMPLETED = "semantic_extraction_completed"
    EVIDENCE_GRAPH_BUILT = "evidence_graph_built"
    CANONICAL_MODEL_BUILT = "canonical_model_built"
    RULE_PACK_APPLIED = "rule_pack_applied"
    MEASUREMENT_COMPLETED = "measurement_completed"
    EXPORT_COMPLETED = "export_completed"
    TELEMETRY_PUBLISHED = "telemetry_published"
    PIPELINE_COMPLETED = "pipeline_completed"
    PIPELINE_FAILED = "pipeline_failed"
```

## Base Event Schema

```python
@dataclass(frozen=True)
class PipelineEvent:
    event_type: EventType
    publisher: str          # handler_id of the publishing handler
    payload: dict           # stage-specific output (varies by event type)
    context: PipelineContext  # snapshot at publication time
    timestamp: datetime     # UTC, set at publication, never modified
```

## Payload Schemas by Event Type

| EventType | Payload Fields | Description |
|-----------|---------------|-------------|
| `REPOSITORY_LOADED` | `{"repository_path": str}` | Resolved repository location |
| `DOCUMENTS_DISCOVERED` | `{"document_count": int, "documents": list[DocumentRef]}` | Discovered spec documents |
| `SEMANTIC_EXTRACTION_COMPLETED` | `{"concept_count": int, "confidence": float}` | Extraction summary |
| `EVIDENCE_GRAPH_BUILT` | `{"node_count": int, "edge_count": int}` | Graph statistics |
| `CANONICAL_MODEL_BUILT` | `{"process_count": int, "entity_count": int}` | CFM element counts |
| `RULE_PACK_APPLIED` | `{"rules_applied": int, "pack_name": str}` | Applied rule pack info |
| `MEASUREMENT_COMPLETED` | `{"methodology": str, "total": float}` | Measurement result summary |
| `EXPORT_COMPLETED` | `{"exported_paths": list[str], "formats": list[str]}` | Exported file paths |
| `TELEMETRY_PUBLISHED` | `{"target": str, "status": str}` | Publish destination and status |
| `PIPELINE_COMPLETED` | `{"total_duration_ms": int}` | Final pipeline summary |
| `PIPELINE_FAILED` | `{"failed_stage": str, "error_message": str}` | Failure details |

## Design Rules

1. Events are frozen (immutable) — no field may change after construction.
2. Payloads are lightweight summaries. Full artifacts live in the Pipeline Context.
3. New event types may be added without breaking existing handlers (handlers
   subscribe only to the types they handle).
4. Event ordering follows the canonical pipeline sequence. The Pipeline Engine
   validates this order and rejects out-of-sequence publications.
