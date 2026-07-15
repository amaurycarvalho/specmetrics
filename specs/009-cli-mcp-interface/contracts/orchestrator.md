# Pipeline Orchestrator Contract

## Purpose

The Pipeline Orchestrator is the shared component that both CLI commands and MCP tools call to execute the measurement pipeline. It ensures behavioral consistency (FR-015) across all interfaces.

## Interface

```python
class PipelineOrchestrator:
    def execute(self, request: PipelineRequest) -> PipelineResult:
        ...
```

The orchestrator:
1. Validates the `PipelineRequest` (mutual exclusion, path existence)
2. Resolves stage names to pipeline event constants
3. Invokes the Kernel Pipeline Engine (002) with the selected stages
4. Collects stage results and the final measurement
5. Invokes the Export Layer (F10) if `output_format` is specified
6. Returns a `PipelineResult`

## Pipeline Event Mapping

The orchestrator maps CLI/MCP stage names to the pipeline events defined in the Kernel Pipeline Engine:

| Stage Name | Kernel Pipeline Event | Produced By |
|-----------|----------------------|-------------|
| `discover` | `RepositoryLoaded` | Specification Adapter |
| `extract` | `DocumentsDiscovered` | Semantic Extraction |
| `graph` | `SemanticExtractionCompleted` | Evidence Graph |
| `cfm` | `EvidenceGraphBuilt` | Canonical Functional Model |
| `rule` | `CanonicalModelBuilt` | Rule Pack Engine |
| `measure` | `RulePackApplied` | Measurement Engine |
| `export` | `MeasurementCompleted` | Export Layer |

## Behavior Matrix

| CLI Flag | MCP Param | Orchestrator Behavior |
|----------|-----------|----------------------|
| *(none)* | *(none)* | Run full pipeline (discover → export) |
| `--stage extract` | — | Run only the `extract` stage |
| `--from measure` | `from_stage: "measure"` | Start from `measure`; skip prior stages |
| `--output json` | `output_format: "json"` | Run full pipeline; format and write export |
| `--quiet` | — | Suppress progress callbacks (CLI-only) |

## Error Handling

- **Invalid stage name**: Return `PipelineResult(status="failed", error="Unknown stage: 'invalid'. Valid stages: discover, extract, graph, cfm, rule, measure, export")`
- **Project not found**: Return `PipelineResult(status="failed", error="Project path not found: /path")`
- **Plugin failure mid-pipeline**: Return `PipelineResult(status="partial", error="Stage 'extract' failed: ...")`
- **Export failure**: Return `PipelineResult(status="partial", error="Pipeline succeeded but export failed: ...")`
