# Contract: Measurement Plugin Interface (SNAP)

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
snap = "specmetrics.plugins.measurement.snap:SNAPMeasurementPlugin"
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
        
        Returns a string like "snap", "sfp", "fpa" that uniquely identifies
        the measurement methodology. Used for registry lookup and logging.
        """

    def supported_methodology(self) -> str:
        """Human-readable name of the measurement methodology.
        
        Returns a string like "SNAP (Software Non-functional Assessment Process)".
        Used for display, documentation, and CLI output.
        """

    def supported_function_types(self) -> list[str]:
        """Assessment category IDs supported by this methodology.
        
        Returns list of category identifiers,
        e.g. ["presentation", "data_operations", "operational_capabilities", "technical_interaction"].
        Used for pre-validation and reporting.
        """

    def measure(
        self,
        cfm: CanonicalFunctionalModel,
        rule_pack: Optional[RulePack] = None,
    ) -> SNAPMeasurementResult:
        """Execute deterministic SNAP assessment on the given CFM.
        
        Args:
            cfm: The Canonical Functional Model (F06) — sole semantic input.
                 Must be fully built and validated with semantic metadata.
            rule_pack: Optional organizational Rule Pack (from F09).
                       If None, default SNAP assessment rules are used.
        
        Returns:
            SNAPMeasurementResult with complete assessment, category breakdowns,
            evidence trails, and any warnings/errors encountered.
        
        Raises:
            InvalidInputError: If cfm is None or fails validation.
            MeasurementError: If a fatal error prevents assessment.
        """
```

### Pipeline Event Contract

The Measurement Plugin is invoked via the event-driven pipeline:

| Event | Emitter | Consumer | Payload |
|-------|---------|----------|---------|
| `RulePackApplied` | Rule Pack Engine (F09) | Pipeline Engine → Measurement Plugin | `cfm` + `rule_pack` in pipeline context |
| `MeasurementCompleted` | Measurement Plugin | Pipeline Engine → downstream stages | `SNAPMeasurementResult` in pipeline context |

### Output Contract

The measurement output (`SNAPMeasurementResult`) must be consumable by:

| Downstream Consumer | Required Format | Contract |
|--------------------|-----------------|----------|
| Export Layer (F10) | Structured model (Pydantic) | `model_dump()` → JSON dict |
| Publisher (F11) | Structured model (Pydantic) | `model_dump()` → OpenTelemetry attributes |
| CLI (F08) | Structured model + text summary | `summary` section for human display |
| MCP (F12) | Structured model | Tool response serialization |

## Rule Pack Contract

Measurement plugins consume Rule Packs (from F09) in this format:

```yaml
# Example Rule Pack for SNAP customization
rule_pack:
  id: "my-org-snap-rules-v1"
  methodology: "SNAP"
  
  # Override contribution values per category
  contribution_overrides:
    presentation: 5.0            # default: sourced from IFPUG SNAP spec
    data_operations: 4.0         # default: sourced from IFPUG SNAP spec
    operational_capabilities: 7.0
    technical_interaction: 6.0
  
  # Exclude entire assessment categories
  excluded_categories:
    - "technical_interaction"
  
  # Exclude individual assessment items by CFM element ID or pattern
  item_exclusions:
    by_id: ["cfm_element_42"]
    by_pattern: ["*internal_*"]
  
  # Redefine inclusion policies (semantic marker → category mapping)
  inclusion_policies:
    - semantic_marker: "custom_ui_feature"
      category: "presentation"
    - semantic_marker: "batch_processing"
      category: "data_operations"
```

When F09 is not yet available, Rule Packs can be loaded directly from YAML files. The SNAP Measurement Engine applies defaults for any unspecified field.
