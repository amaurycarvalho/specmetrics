# Contract: Measurement Plugin Interface

## Overview

Defines the plugin interface that all measurement engine plugins (including APF) must implement to integrate with the SpecMetrics Kernel and Plugin Registry. This contract enables any measurement methodology (APF, SPF, SNAP, etc.) to be developed as an independent, discoverable plugin.

## Discovery & Registration

### Entry Point Group

```text
specmetrics.plugins.measurement
```

Each measurement plugin package declares this entry point in its `pyproject.toml`:

```toml
[project.entry-points."specmetrics.plugins.measurement"]
apf = "specmetrics.plugins.measurement.apf:APFMeasurementPlugin"
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
        
        Returns a string like "apf", "spf", "snap" that uniquely identifies
        the measurement methodology. Used for registry lookup and logging.
        """

    def supported_methodology(self) -> str:
        """Human-readable name of the measurement methodology.
        
        Returns a string like "IFPUG/APF Function Point Analysis".
        Used for display, documentation, and CLI output.
        """

    def supported_function_types(self) -> list[str]:
        """Function type codes supported by this methodology.
        
        Returns list of function type identifiers, e.g. ["ILF", "EIF", "EI", "EO", "EQ"].
        Used for pre-validation and reporting.
        """

    def measure(
        self,
        cfm: CanonicalFunctionalModel,
        rule_pack: Optional[RulePack] = None,
    ) -> APFMeasurementResult:
        """Execute deterministic measurement on the given CFM.
        
        Args:
            cfm: The Canonical Functional Model (F06) — sole semantic input.
                 Must be fully built and validated.
            rule_pack: Optional organizational Rule Pack (from F09).
                       If None, default IFPUG counting rules are used.
        
        Returns:
            APFMeasurementResult with complete measurement, evidence trails,
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
| `MeasurementCompleted` | Measurement Plugin | Pipeline Engine → downstream stages | `APFMeasurementResult` in pipeline context |

### Output Contract

The measurement output (`APFMeasurementResult`) must be consumable by:

| Downstream Consumer | Required Format | Contract |
|--------------------|-----------------|----------|
| Export Layer (F10) | Structured model (Pydantic) | `model_dump()` → JSON dict |
| Publisher (F11) | Structured model (Pydantic) | `model_dump()` → OpenTelemetry attributes |
| CLI (F08) | Structured model + text summary | `summary` section for human display |
| MCP (F12) | Structured model | Tool response serialization |

## Rule Pack Contract

Measurement plugins consume Rule Packs (from F09) in this format:

```yaml
# Example Rule Pack for APF customization
rule_pack:
  id: "my-org-apf-rules-v1"
  methodology: "APF"
  
  # Override complexity matrix boundaries per function type
  complexity_overrides:
    ILF:
      ret_boundaries: [1, 2, 6]      # default: [1, 2, 6]
      det_boundaries: [19, 50]        # default: [19, 50]
    EI:
      ftr_boundaries: [1, 2, 3]       # default: [0, 2, 3]
      det_boundaries: [4, 15]          # default: [4, 15]
    # ... (EO, EQ follow same pattern)
  
  # Override UFP weight table
  weight_overrides:
    ILF:
      Low: 7
      Average: 10
      High: 15
  
  # Exclude entire function types
  excluded_types: []  # e.g., ["EQ"] to exclude inquiries
  
  # Exclude specific CFM elements by ID
  element_exclusions:
    by_id: []         # e.g., ["data_group_17"]
    by_pattern: []    # e.g., ["*_internal_*"]
  
  # Value Adjustment Factor (optional)
  vaf:
    gsc_ratings:      # 14 General System Characteristics, each 0-5
      data_communications: 3
      distributed_data: 2
      performance: 4
      # ... (all 14 GSCs)
```

When F09 is not yet available, Rule Packs can be loaded directly from YAML files. The Measurement Engine applies defaults for any unspecified field.
