# Implementation Plan: CLI & MCP Interaction Layer

**Branch**: `009-cli-mcp-interface` | **Date**: 2026-07-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/009-cli-mcp-interface/spec.md`

## Summary

Provide both human (CLI) and machine (MCP Server) interfaces to the SpecMetrics measurement pipeline. Users execute `specmetrics measure` for a complete pipeline run; AI agents invoke the same pipeline programmatically through the Model Context Protocol. Both interfaces share a unified pipeline orchestrator, ensuring behavioral consistency while operating independently.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: Typer (CLI framework), `mcp` Python package (MCP server), structlog (logging), Pydantic v2 (models/schemas)

**Storage**: N/A — no persistent storage; reads/writes project filesystem paths provided by user

**Testing**: pytest with Typer CLI test runner; MCP test client for protocol-level tests

**Target Platform**: Linux (primary), macOS (secondary)

**Project Type**: CLI tool + MCP server (co-located in same package; independent entry points)

**Performance Goals**: Full pipeline in <30s for standard projects (as specified SC-001); MCP server starts and accepts connections in <5s (SC-005)

**Constraints**: CLI and MCP operate independently (FR-016); MCP uses stdio transport (FR-013); no authentication for MVP; single MCP client at a time

**Scale/Scope**: Single project measurement per invocation; single MCP client session

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**: X (AI-Friendly by Design), VII (Canonical Representation), VIII (Plugin-Oriented), XI (Observability), XIV (Layer Independence)

### Compliance Verifications
- [x] Specification First: CLI/MCP consume spec-driven outputs (CFM, measurement results) — they do not bypass specifications
- [x] Evidence First: Both interfaces pass through evidence-preserving measurement results without stripping provenance
- [x] Canonical Representation: Both interfaces consume only the Canonical Functional Model and measurement results — no framework-specific artifacts
- [x] Plugin-Oriented: CLI commands and MCP tools registered via platform command registry; new pipeline stages automatically available
- [x] Rule Externalization: N/A — interaction layer does not define measurement policies
- [x] Layer Independence: Interaction layer depends only on pipeline orchestration contracts — not on internal pipeline implementation
- [x] Open by Default: CLI uses standard POSIX conventions; MCP uses open JSON-RPC 2.0 protocol

## Project Structure

### Documentation (this feature)

```text
specs/009-cli-mcp-interface/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Created by /speckit.tasks
```

### Source Code (repository root)

```text
specmetrics/
├── cli/
│   ├── __init__.py
│   ├── app.py              # Typer app, command definitions, help
│   ├── measure.py          # `specmetrics measure` command handler
│   ├── plugins.py          # `specmetrics plugins` command handler
│   └── formatters.py       # Output formatting (text table, JSON, progress)
├── mcp/
│   ├── __init__.py
│   ├── server.py           # MCP server process, JSON-RPC handling
│   └── tools.py            # MCP tool implementations (measure, plugins/list, version)
├── application/
│   └── orchestrator.py     # Shared pipeline orchestrator (CLI and MCP both use this)
└── tests/
    ├── cli/
    │   ├── test_app.py
    │   ├── test_measure.py
    │   └── test_formatters.py
    ├── mcp/
    │   ├── test_server.py
    │   └── test_tools.py
    └── application/
        └── test_orchestrator.py
```

**Structure Decision**: Single-project layout with `cli/`, `mcp/`, and `application/` subpackages under `specmetrics/`. Tests mirror the source layout. The `application/` package contains the shared orchestrator that both CLI commands and MCP tools consume, ensuring FR-015 (consistent behavior across interfaces).

## Complexity Tracking

No constitution violations detected — the design satisfies all engaged principles without complexity trade-offs.
