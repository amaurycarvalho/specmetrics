# Implementation Plan: Plugin Discovery & Registry

**Branch**: `003-plugin-discovery-registry` | **Date**: 2026-07-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-plugin-discovery-registry/spec.md`

## Summary

Implement the Plugin Discovery and Registry subsystem that discovers SpecMetrics
plugins via Python Entry Points, validates their compatibility, and exposes a
registry for the Pipeline Engine (F01) to resolve event handlers. The registry
is an independent component — owned by neither the Kernel nor the Application
Layer.

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**: `importlib.metadata` (stdlib), structlog (existing),
pytest (testing)

**Storage**: N/A — registry is in-memory; no persistence required

**Testing**: pytest (unit for discovery + validation + registry; integration for
end-to-end plugin loading)

**Target Platform**: Linux

**Project Type**: library (kernel module)

**Performance Goals**: Full discovery of 50 plugins completes within 5 seconds
(SC-005); handler lookup completes within 100ms (SC-004)

**Constraints**: Python Entry Points only as discovery mechanism; no custom
plugin format or package manager; no runtime discovery (requires restart);
plugins isolated at import level

**Scale/Scope**: 50+ simultaneously installed plugins; each plugin may handle
0+ event types

## Constitution Check

*GATE: Phase 0 research complete. Post-design re-check passed.*

**Engaged Principles**: VIII (Plugin-Oriented), XII (Open by Default),
XIII (Evolution Without Disruption)

**Compliance Verifications**:
- [x] Plugin-Oriented: All extension points are discovered through the same
  unified mechanism (Python Entry Points); the core platform never hard-codes
  plugin references
- [x] Open by Default: Python Entry Points are a documented open standard;
  plugin metadata is validated through public interfaces; any Python package
  can declare a SpecMetrics plugin
- [x] Evolution Without Disruption: API version validation (SemVer) ensures
  plugins built for incompatible versions are rejected before they can cause
  runtime failures

**Gate result**: PASS — all principles satisfied.

**Research Resolution**:
- Entry point schema: Factory function pattern (`module:register`) returning
  `PluginMetadata` dataclass (see [research.md](research.md#1-entry-point-metadata-schema))
- API version source: `importlib.metadata.version("specmetrics")` (see
  [research.md](research.md#2-platform-api-version-source))
- F01 integration: PluginRegistry.install_handlers() populates HandlerRegistry
  (see [research.md](research.md#3-integration-with-f01-handlerregistry))

## Project Structure

### Documentation (this feature)

```text
specs/003-plugin-discovery-registry/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── plugin-entry-point.md
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
specmetrics/
├── kernel/
│   ├── __init__.py
│   ├── plugin_registry.py       # NEW — PluginRegistry, PluginDescriptor
│   ├── plugin_discovery.py      # NEW — Entry point scanning, loading
│   ├── plugin_validation.py     # NEW — API version, interface checks
│   ├── plugin_metadata.py       # NEW — PluginMetadata model
│   └── ... (existing F01 files)
└── tests/
    ├── unit/
    │   ├── test_plugin_discovery.py   # NEW
    │   ├── test_plugin_validation.py  # NEW
    │   └── test_plugin_registry.py    # NEW
    └── integration/
        └── test_plugin_lifecycle.py   # NEW
```

**Structure Decision**: Plugin discovery lives in `specmetrics/kernel/` because
it is a core infrastructure component consumed by the Pipeline Engine. The
registry is independent from F01's HandlerRegistry but integrates with it.

## Complexity Tracking

No constitution violations expected. The plugin discovery mechanism is a
standard Python pattern (importlib.metadata + factory functions). API version
validation is the only non-trivial logic, and it follows simple SemVer rules.
