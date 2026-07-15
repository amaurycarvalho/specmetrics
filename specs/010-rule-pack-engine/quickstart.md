# Quickstart: Rule Pack Engine

## Prerequisites

- Python >= 3.12
- Project dependencies installed (`pip install -e ".[dev]"`)
- Kernel Pipeline Engine (002) and Plugin Discovery Registry (003) available
- Canonical Functional Model (007) published as `specmetrics.kernel.cfm.model.CanonicalFunctionalModel`

## Setup

### 1. Create Rule Pack files

```bash
mkdir -p .specify/rules
```

Create `.specify/rules/example.yml`:

```yaml
id: "example-v1"
description: "Example Rule Pack for validation"

rules:
  - id: "exclude-eq"
    type: "exclusion"
    description: "Exclude External Inquiries from counting"
    config:
      function_types: ["EQ"]

  - id: "strict-ei-complexity"
    type: "complexity_override"
    description: "Lower threshold for High complexity on External Inputs"
    config:
      function_type: "EI"
      thresholds:
        det: [2, 8]
        ftr: [1, 2]

  - id: "vaf-default"
    type: "vaf"
    description: "Standard VAF with neutral GSC ratings"
    config:
      gsc:
        data_communications: 2
        distributed_data_processing: 2
        performance: 2
        heavily_used_configuration: 2
        transaction_rate: 2
        online_data_entry: 2
        end_user_efficiency: 2
        online_update: 2
        complex_processing: 2
        reusability: 2
        installation_ease: 2
        operational_ease: 2
        multiple_sites: 2
        facilitate_change: 2
```

### 2. Create a test CFM fixture

The Rule Pack Engine consumes a `CanonicalFunctionalModel`. For validation, create a fixture CFM with known functions.

## Validation Scenarios

### Scenario 1: Basic Rule Pack Loading

**Goal**: Verify the engine discovers and loads Rule Pack files.

```bash
# Run via pipeline
python -c "
from specmetrics.kernel.pipeline_engine import PipelineEngine
from specmetrics.kernel.handler_registry import HandlerRegistry
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.plugins.rule_pack.plugin import RulePackEnginePlugin

registry = HandlerRegistry()
engine = RulePackEnginePlugin()
registry.register(engine)

pipeline = PipelineEngine(registry)
ctx = PipelineContext()
result = pipeline.run(ctx)
print('Rule Pack Engine stage executed:', result.diagnostics)
"
```

**Expected outcome**: Diagnostics show the `RULE_PACK_APPLIED` stage completed with loaded rules.

### Scenario 2: Exclusion Rule Application

**Goal**: Verify exclusion rules are applied to the CFM.

```python
from specmetrics.kernel.cfm.model import CanonicalFunctionalModel, FunctionalProcess, EvidenceRef
from specmetrics.kernel.cfm.metadata import BuildMetadata
from specmetrics.plugins.rule_pack.plugin import RulePackEnginePlugin

# Create CFM with known EQs
cfm = CanonicalFunctionalModel(
    run_id="test-001",
    functional_processes={
        "fp-001": FunctionalProcess(id="fp-001", name="User Login", evidence=EvidenceRef(graph_node_id="n1", document_id="doc-1", text="...")),
        "fp-002": FunctionalProcess(id="fp-002", name="Generate Report", evidence=EvidenceRef(graph_node_id="n2", document_id="doc-1", text="...")),
    },
    metadata=BuildMetadata(...)
)

result = engine.apply_rules(cfm)
# Verify fp-002 is marked as excluded by the "exclude-eq" rule
assert result.get_element("fp-002").metadata["excluded_by"] == "example-v1/exclude-eq"
```

**Expected outcome**: Functions matching exclusion rules are annotated with `excluded_by` metadata referencing the specific rule.

### Scenario 3: Invalid Rule Pack Handling

**Goal**: Verify the engine gracefully handles invalid Rule Packs.

```bash
# Create invalid Rule Pack
echo 'id: "bad-pack"' > .specify/rules/bad.yml
echo 'rules:' >> .specify/rules/bad.yml
echo '  - id: "bad-rule"' >> .specify/rules/bad.yml
echo '    type: "exclusion"' >> .specify/rules/bad.yml
echo '    config:' >> .specify/rules/bad.yml
echo '      function_types: ["UNKNOWN"]' >> .specify/rules/bad.yml

# Run pipeline
python -c "
from specmetrics.plugins.rule_pack.validator import RulePackValidator
validator = RulePackValidator()
report = validator.validate_file('.specify/rules/bad.yml')
assert len(report.errors) == 1
assert 'UNKNOWN' in report.errors[0].message
print('Validation correctly rejected invalid function type')
"
```

**Expected outcome**: The validator reports an error for `UNKNOWN` function type. The pipeline continues without crashing; the bad rule is skipped and logged.

### Scenario 4: Determinism Verification

**Goal**: Verify the engine produces identical output for identical inputs.

```python
cfm = create_test_cfm()
rule_pack_dir = ".specify/rules/"

result1 = engine.run(cfm, rule_pack_dir)
result2 = engine.run(cfm, rule_pack_dir)

# Assert byte-identical output
import json
assert json.dumps(result1.model_dump(), sort_keys=True) == json.dumps(result2.model_dump(), sort_keys=True)
```

**Expected outcome**: Both runs produce identical annotated CFM.

### Scenario 5: Empty Rules Directory

**Goal**: Verify the engine works with no Rule Pack files.

```bash
# Ensure .specify/rules/ is empty
rm -f .specify/rules/*.yml

python -c "
from specmetrics.plugins.rule_pack.plugin import RulePackEnginePlugin
engine = RulePackEnginePlugin()
cfm = create_test_cfm()
result = engine.apply_rules(cfm)
# CFM should pass through unmodified
assert result == cfm  # or assert no annotations added
print('Empty rules: CFM passed through unmodified')
"
```

**Expected outcome**: CFM passes through unmodified with a log message indicating no active rules.

## Running the Full Test Suite

```bash
# Run unit tests for the Rule Pack Engine plugin
pytest tests/plugins/rule_pack/ -v

# Run with coverage
pytest tests/plugins/rule_pack/ --cov=specmetrics.plugins.rule_pack -v
```

## Linking to Design Artifacts

| Artifact | Path |
|----------|------|
| Data model | [data-model.md](data-model.md) |
| Rule Pack file contract | [contracts/README.md](contracts/README.md) |
| Pipeline stage contract | [contracts/README.md#pipeline-stage-contract](contracts/README.md#pipeline-stage-contract) |
| Implementation plan | [plan.md](plan.md) |
| Feature specification | [spec.md](spec.md) |
