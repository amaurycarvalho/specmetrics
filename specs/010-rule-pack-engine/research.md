# Research: Rule Pack Engine

## Architectural Decisions

### Decision 1: Rule Pack Format

- **Decision**: YAML, using ruamel.yaml
- **Rationale**: The project already depends on ruamel.yaml for configuration. YAML supports comments, anchors, and complex nested structures needed for exclusion rules, thresholds, and VAF configuration. The existing `RulePack` model in the FPA measurement plugin already demonstrates the structure.
- **Alternatives considered**: JSON (no comment support, less readable for policy files), TOML (limited nesting, less suitable for complex rule definitions), Python code (violates Principle IX - Rule Externalization)

### Decision 2: Pipeline Integration Pattern

- **Decision**: Implement as an EventHandler registered for `EventType.RULE_PACK_APPLIED`, following the existing pattern used by other pipeline stages
- **Rationale**: The pipeline engine already iterates through `CANONICAL_EVENT_ORDER` which includes `EventType.RULE_PACK_APPLIED`. The HandlerRegistry and EventBus infrastructure is fully in place. This approach requires zero changes to the pipeline engine.
- **Alternatives considered**: Standalone CLI command (would bypass pipeline integration), direct call from measurement plugin (would violate Layer Independence)

### Decision 3: Rule Pack Model Location

- **Decision**: Extract `RulePack` model from `specmetrics.plugins.measurement.fpa.models` to `specmetrics.kernel.cfm.models` as a shared contract
- **Rationale**: Both the Rule Pack Engine (producer) and Measurement Engine (consumer) need the same model. Placing it in the kernel's CFM module makes it a stable, published contract. The measurement plugin imports from the new shared location; backward compatibility is maintained with a re-export.
- **Alternatives considered**: Keep model in measurement plugin (creates circular dependency), duplicate the model (maintenance burden), create a separate `specmetrics.models` package (over-engineered for one model)

### Decision 4: CFM Annotation Strategy

- **Decision**: Add an `applied_rules: dict[str, list[AppliedRule]]` field to the `CanonicalFunctionalModel` metadata, plus a `CFMConsumer` extension that accepts annotated CFM
- **Rationale**: The CFM is frozen and cannot be mutated in-place. Adding applied rules as metadata preserves immutability while enabling traceability. The Measurement Engine's `CFMConsumer` protocol already accepts CFM, so downstream plugins read the annotations without coupling to the Rule Pack Engine.
- **Alternatives considered**: Unfreeze CFM and add rule annotations directly (violates immutability invariant), create a separate `AnnotatedCFM` wrapper (adds unnecessary complexity), serialize annotations in a parallel structure (harder to trace)

### Decision 5: Rule Pack File Layout

- **Decision**: One or more `.yml` files in `.specmetrics/rules/`, each self-contained with its own `id`, `description`, and rules
- **Rationale**: Multiple files allow teams to organize rules by domain, methodology, or project phase. Each file is independently loadable and validatable. File-level conflict resolution (last-loaded wins) is simple and predictable.
- **Alternatives considered**: Single `rule-pack.yml` (becomes unwieldy with many rules), single JSON file in `.specify/init-options.json` (mixes policy with project config), directory with subdirectories per methodology (over-engineered for v1)

### Decision 6: VAF and GSC Handling

- **Decision**: The Rule Pack Engine computes VAF from GSC ratings and annotates the CFM with the computed VAF; the Measurement Engine reads it from annotations
- **Rationale**: VAF computation follows a deterministic formula (0.65 + 0.01 * sum(GSC)). Keeping it in the Rule Pack Engine ensures all policy-related computation is in one layer. The measurement plugin's existing `compute_vaf` logic moves to the engine.
- **Alternatives considered**: Keep VAF computation in measurement engine (duplicates policy logic), defer VAF to a separate stage (unnecessary pipeline complexity)

## Existing Code Analysis

### Current RulePack Model (in measurement plugin)

```python
class RulePack(BaseModel):
    id: str
    methodology: str = "FPA"
    complexity_overrides: Optional[dict[str, dict[str, list[int]]]] = None
    weight_overrides: Optional[dict[str, dict[str, int]]] = None
    excluded_types: list[FunctionType] = []
    element_exclusions: Optional[dict[str, list[str]]] = None
    vaf: Optional[dict[str, int]] = None
```

The model is already well-structured but lacks:
- `rules: list[Rule]` for per-rule traceability (each rule needs an ID for FR-008 annotation)
- `glossary_overrides` for terminology customization (FR-012)
- Validation logic for rule conflicts (FR-006)

### Existing RulePackApplicator (in measurement plugin)

The applicator resolves weight overrides, excluded types, complexity overrides, VAF, and element exclusions. This logic will be migrated to the new Rule Pack Engine, and the measurement plugin will consume the annotated CFM instead of applying rules directly.

### Pipeline Integration Points

- `EventType.RULE_PACK_APPLIED` — already defined in `events.py`
- `CANONICAL_EVENT_ORDER[5]` — already positioned between CANONICAL_MODEL_BUILT and MEASUREMENT_COMPLETED
- `PipelineContext.canonical_model` — the engine reads CFM from this field and writes annotated CFM back
- `EventHandler` protocol — the engine implements `handled_event_type`, `handler_id`, `stage_name`, and `handle`

## Dependency Map

```
┌──────────────────────┐
│  .specmetrics/rules/*.yml│  (Rule Pack files)
└────────┬─────────────┘
         │ loaded by
         ▼
┌──────────────────────┐
│  Rule Pack Engine    │  plugins/rule_pack/
│  (EventHandler)      │
└────────┬─────────────┘
         │ produces annotated CFM
         ▼
┌──────────────────────┐
│  Measurement Engine  │  plugins/measurement/fpa/
│  (reads annotations) │
└──────────────────────┘
```

No circular dependencies. The Rule Pack Engine depends on:
- `specmetrics.kernel.cfm.model.CanonicalFunctionalModel`
- `specmetrics.kernel.cfm.models.RulePack` (new shared location)
- `specmetrics.kernel.events.EventType`
- `specmetrics.kernel.handler_registry.EventHandler`
- `ruamel.yaml` (Rule Pack file parsing)
- `structlog` (logging)

## Validation Strategy

- **Unit tests**: Each component (loader, validator, applicator, annotator) tested independently with fixture Rule Pack files and mock CFM
- **Integration tests**: Full pipeline test with Plugin Registry, HandlerRegistry, PipelineEngine — verify RULE_PACK_APPLIED event fires and annotations appear in output
- **Edge case tests**: Invalid YAML, conflicting rules, empty rules directory, missing required fields, unsupported function types
- **Determinism tests**: Run the same CFM + Rule Pack twice, assert byte-identical output
