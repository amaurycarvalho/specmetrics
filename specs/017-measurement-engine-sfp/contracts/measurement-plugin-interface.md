# Contract: Measurement Plugin Interface (SFP)

## Overview

Defines the plugin interface that all measurement engine plugins must implement to integrate with the SpecMetrics Kernel and Plugin Registry. This contract enables any measurement methodology (FPA, SFP, SNAP, etc.) to be developed as an independent, discoverable plugin.

## Discovery & Registration

### Entry Point Group

```text
specmetrics.plugins.measurement
```

Each measurement plugin package declares this entry point in its `pyproject.toml`:

```toml
[project.entry-points."specmetrics.plugins.measurement"]
sfp = "specmetrics.plugins.measurement.sfp:SFPMeasurementPlugin"
```

### Plugin Lifecycle

1. **Discovery**: Plugin Registry scans `specmetrics.plugins.measurement` entry points at startup
2. **Validation**: Registry validates the plugin satisfies the `MeasurementPlugin` protocol
3. **Registration**: Plugin is registered and available for pipeline orchestration
4. **Invocation**: Pipeline Engine calls `plugin.measure(cfm, rule_pack)` at the measurement stage
5. **Teardown**: No persistent state — plugin instances are stateless per invocation

## Interface Protocol

### `MeasurementPlugin`

```python
class MeasurementPlugin(Protocol):
    """Protocol that all measurement engine plugins must satisfy."""

    def plugin_id(self) -> str:
        """Unique identifier for this measurement plugin.
        
        Returns a string like "sfp", "fpa", "snap" that uniquely identifies
        the measurement methodology. Used for registry lookup and logging.
        """

    def supported_methodology(self) -> str:
        """Human-readable name of the measurement methodology.
        
        Returns a string like "Simple Function Points (SFP)".
        Used for display, documentation, and CLI output.
        """

    def supported_component_types(self) -> list[str]:
        """Component type codes supported by this methodology.
        
        Returns list of component type identifiers,
        e.g. ["functional_process", "logical_function"].
        Used for pre-validation and reporting.
        """

    def measure(
        self,
        cfm: CanonicalFunctionalModel,
        rule_pack: Optional[RulePack] = None,
    ) -> SFPMeasurementResult:
        """Execute deterministic measurement on the given CFM.
        
        Args:
            cfm: The Canonical Functional Model (F06) — sole semantic input.
                 Must be fully built and validated.
            rule_pack: Optional organizational Rule Pack (from F09).
                       If None, default SFP counting rules are used.
        
        Returns:
            SFPMeasurementResult with complete measurement, evidence trails,
            and any warnings/errors encountered.
        
        Raises:
            InvalidInputError: If cfm is None or fails validation.
            MeasurementError: If a fatal error prevents measurement.
        """
```

### Pipeline Event Contract

The Measurement Plugin is invoked via the event-driven pipeline:

| Event | Emitter | Consumer | Payload |
|-------|---------|----------|---------|
| `RulePackApplied` | Rule Pack Engine (F09) | Pipeline Engine → Measurement Plugin | `cfm` + `rule_pack` in pipeline context |
| `MeasurementCompleted` | Measurement Plugin | Pipeline Engine → downstream stages | `SFPMeasurementResult` in pipeline context |

### Output Contract

The measurement output (`SFPMeasurementResult`) must be consumable by:

| Downstream Consumer | Required Format | Contract |
|--------------------|-----------------|----------|
| Export Layer (F10) | Structured model (Pydantic) | `model_dump()` → JSON dict |
| Publisher (F11) | Structured model (Pydantic) | `model_dump()` → OpenTelemetry attributes |
| CLI (F08) | Structured model + text summary | `summary` section for human display |
| MCP (F12) | Structured model | Tool response serialization |

## Rule Pack Contract

Measurement plugins consume Rule Packs (from F09) in this format:

```yaml
# Example Rule Pack for SFP customization
rule_pack:
  id: "my-org-sfp-rules-v1"
  methodology: "SFP"
  
  # Override fixed contribution values per component type
  contribution_overrides:
    functional_process: 5.0    # default: sourced from IFPUG SFP spec
    logical_function: 7.5      # default: sourced from IFPUG SFP spec
  
  # Exclude entire component types
  excluded_types: []  # e.g., ["logical_function"] to exclude LFs
  
  # Redefine inclusion criteria per component type
  inclusion_criteria:
    functional_process:
      node_types: ["elementary_process"]
      semantic_types: []
    logical_function:
      node_types: ["data_group"]
      semantic_types: ["business_entity"]
  
  # Exclude specific CFM elements by ID or pattern
  element_exclusions:
    by_id: []         # e.g., ["data_group_17"]
    by_pattern: []    # e.g., ["*_internal_*"]
  
  # Include additional elements by ID or pattern
  element_inclusions:
    by_id: []
    by_pattern: []
```

When F09 is not yet available, Rule Packs can be loaded directly from YAML files. The SFP Measurement Engine applies defaults for any unspecified field.
