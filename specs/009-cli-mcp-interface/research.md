# Research: CLI & MCP Interaction Layer

## Research Tasks

| # | Topic | Source | Investigation |
|---|-------|--------|---------------|
| 1 | MCP Python SDK selection | Technical Context — Primary Dependencies | Evaluate official MCP Python SDK vs alternatives |
| 2 | CLI human-readable output format | Spec FR-003, FR-004 | Determine summary format for terminal display |
| 3 | Stage naming and pipeline mapping | Spec FR-006, FR-007 | Map stage names to pipeline event names |

---

## 1. MCP Python SDK

**Decision**: Use `mcp` (modelcontextprotocol/python-sdk v1.x)

**Rationale**: The official Model Context Protocol Python SDK (`mcp`) is the reference implementation maintained by Anthropic. It provides:
- Stdio transport support (required by FR-013)
- JSON-RPC 2.0 message handling built-in
- Tool registration decorators matching the spec's tool requirements
- Server initialization handshake (FR-020)
- Structured error responses (FR-014)
- Active maintenance and community adoption

**Alternatives considered**:
- Custom JSON-RPC implementation: Avoided — reinventing protocol handling adds risk and maintenance burden
- `mcp-fastmcp`: Higher-level abstraction but less control over transport details needed for stdio-only MVP

**Integration**: The MCP server wraps the same `application/orchestrator.py` that the CLI uses. MCP tool handlers are thin adapters that parse MCP request arguments, call orchestrator methods, and format responses.

---

## 2. CLI Human-Readable Output Format

**Decision**: Multi-section text format with structured tables

**Rationale**: Terminal output should provide at-a-glance comprehension for quality engineers and CI/CD logs. The format uses:

```
SpecMetrics v0.1.0 — Measurement Complete
────────────────────────────────────────
Project: /home/user/my-project
Pipeline: full (8 stages)
Duration: 12.4s

Results:
  Total Function Points: 145
  ├── ILF: 5 (Low: 3, Avg: 2)
  ├── EIF: 2 (Low: 2)
  ├── EI:  8 (Low: 4, Avg: 3, High: 1)
  ├── EO:  3 (Low: 2, Avg: 1)
  └── EQ:  4 (Low: 3, Avg: 1)

Stages:
  ✓ Discovery        (0.3s)
  ✓ Extraction       (7.1s)
  ✓ Evidence Graph   (0.8s)
  ✓ CFM              (0.5s)
  ✓ Rule Pack        (0.2s)
  ✓ Measurement      (2.5s)
  ✓ Export           (0.1s)

Output: /home/user/my-project/specmetrics-output.json
```

- `--quiet` suppresses all output except errors and the final result line
- `--verbose` adds per-stage detail including entity counts
- `--output json` writes machine-readable JSON and prints only the summary header
- Non-zero exit codes print the error context above the summary

**Alternatives considered**:
- JSON-only: unsuitable for interactive terminal use
- Single-line summary: insufficient for understanding stage-level performance
- YAML output: less common for terminal consumption

---

## 3. Stage Naming and Pipeline Mapping

**Decision**: Stage names match the pipeline event constants defined in Kernel Pipeline Engine (002)

**Rationale**:
The pipeline stages defined in the constitution's pipeline events serve as the canonical stage names:

| `--stage` / `--from` value | Pipeline Event | Description |
|---|---|---|
| `discover` | RepositoryLoaded | Specification discovery |
| `extract` | DocumentsDiscovered | Semantic extraction |
| `graph` | SemanticExtractionCompleted | Evidence graph build |
| `cfm` | EvidenceGraphBuilt | Canonical model build |
| `rule` | CanonicalModelBuilt | Rule pack application |
| `measure` | RulePackApplied | Measurement execution |
| `export` | MeasurementCompleted | Export formatting |

- `--stage <name>` runs ONLY that single stage (requires pre-existing inputs)
- `--from <name>` runs from that stage onwards (skips prior stages)
- `--to <name>` (future) runs up to that stage

The orchestrator maps these names to pipeline event constants. Unknown stage names produce a descriptive error listing valid options.

**Alternatives considered**:
- Numeric stage indices: less readable and error-prone
- Pipeline-order position (1-8): fragile if stages are added
- Full event names (RepositoryLoaded): too verbose for CLI flags
