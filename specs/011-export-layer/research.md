# Research: Export Layer

**Phase 0 output for `/speckit.plan` command**

## Overview

No NEEDS CLARIFICATION markers were present in the spec or technical context. The
constitution and spec provided sufficient guidance for all technical decisions.
This document captures the decisions made, rationale, and alternatives considered.

---

## 1. Serial Per-Format Export Strategy

**Decision**: Export formats are processed sequentially; one format failure does not block others.

**Rationale**: Export targets are <5s for 3 formats on 1,000 functions, making parallel execution
unnecessary for v1. Error isolation ensures partial success (3 of 3, 2 of 3, or 1 of 3 formats)
rather than all-or-nothing. This aligns with the clarification from `/speckit.clarify`.

**Alternatives considered**:
- **Fully concurrent**: Adds complexity (thread safety, resource contention) without user-perceptible
  benefit at v1 scale. Deferred to future if throughput becomes a bottleneck.
- **Fail-fast sequential**: Simpler but loses partial progress. Rejected because users prefer
  some output over none.
- **Queue-based async**: Premature for v1's single-user local execution model.

---

## 2. Plugin Interface Design

**Decision**: Export/publisher plugins use Python abstract base classes registered via
entry points, consistent with the existing plugin discovery mechanism.

**Rationale**: The constitution mandates plugin-oriented architecture (VIII) and the existing
plugin registry already uses Python entry points. Consistency reduces learning curve for
plugin developers.

**Alternatives considered**:
- **Protocol classes (PEP 544)**: More flexible but would diverge from existing plugin patterns.
  Could be introduced later without breaking changes if needed.
- **YAML-declared plugins**: Would require a new registration mechanism. Rejected in favor of
  reusing existing infrastructure.

---

## 3. OpenTelemetry Publisher Strategy

**Decision**: Use the OpenTelemetry SDK API directly for metric publishing. Export layer
publishes metrics as counters (function count per category) and histograms (complexity distribution).

**Rationale**: The constitution specifies OpenTelemetry as the telemetry technology. SDK API
provides standards-compliant output without vendor lock-in. Metrics enable trend visualization
in any OpenTelemetry-compatible backend (Prometheus, Grafana, Datadog, etc.).

**Alternatives considered**:
- **Custom metrics protocol**: Would violate "Open by Default" (XII). Rejected.
- **Vendor-specific SDK**: Lock-in risk. Rejected.

---

## 4. JSON/CSV/XML Serialization Approach

**Decision**: Use Python standard library for all three formats initially.
- JSON: `json` module
- CSV: `csv` module  
- XML: `xml.etree.ElementTree`

**Rationale**: These formats have mature standard library support, zero additional dependencies,
and are sufficient for v1's single-user export scale (10K functions max). If performance
becomes an issue, specialized libraries (orjson, lxml) can be substituted behind the plugin
interface without breaking consumers.

**Alternatives considered**:
- **Third-party libraries (orjson, lxml)**: Higher performance but adds dependencies.
  Deferred until profiling demonstrates a bottleneck.
- **Template-based generation (Jinja2)**: More flexible but heavier. Rejected for v1's
  fixed-format requirements.

---

## 5. Access Control Approach

**Decision**: Rely on OS-level file permissions for export output; no application-level auth.

**Rationale**: v1 deployment is local-only (CLI + MCP Server). The OS user running the CLI
has natural access control via filesystem permissions. Adding application auth would introduce
complexity without a threat model to justify it.

**Alternatives considered**:
- **App-level RBAC**: Premature for single-user local mode. Can be added as a plugin when
  multi-user or server deployment is introduced.
- **No checks at all**: Equivalent to OS-level permissions (the user running the process
  is the only user). Functionally identical for v1.

---

## 6. Output File Management

**Decision**: Overwrite existing files with a warning. Produce valid empty files for
zero-result pipelines.

**Rationale**: These clarifications from `/speckit.clarify` balance automation compatibility
(overwrite for CI scripts) with user awareness (warning log). Empty files keep downstream
tooling happy (no missing-file errors).

**Alternatives considered**:
- **Error on existing file**: Breaks CI scripts. Rejected.
- **Auto-rename**: Creates orphan files over time. Deferred if users request it.
- **Error on zero results**: Breaks dashboards expecting consistent schemas. Rejected.
