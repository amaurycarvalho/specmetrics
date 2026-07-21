# Quickstart: Validating OpenSpec Operation Extraction Rules

**Feature**: 035-openspec-operation-rules

## Prerequisites

- Python 3.12+ virtual environment with `specmetrics` installed (`pip install -e .`)
- No LLM API key configured (forces deterministic fallback)
- OpenSpec test samples at `tests/openspec/`

## Validation Scenarios

### 1. Verify Operation Extraction from OpenSpec Samples (US1)

**Goal**: Confirm the deterministic engine produces operation elements from OpenSpec THEN, AND, SHALL, and DEVE patterns.

**Command**:
```bash
# Run extraction on the OpenSpec test directory
.venv/bin/python3 -c "
from pathlib import Path
from specmetrics.application.orchestrator import PipelineOrchestrator
from specmetrics.application.models import PipelineRequest
from specmetrics.application.enums import OutputFormat

orch = PipelineOrchestrator()
req = PipelineRequest(
    project_path=Path('tests/openspec'),
    output_format=OutputFormat.NONE,
    measure_id='openspec-validation',
)
result = orch.execute(req)
for r in result.metric_results:
    print(f'  {r.name}: {r.total}')
"
```

**Expected outcome**: Story Points > 0, Function Points > 0, Simplified Function Points > 0.

### 2. Verify Rule Type Changes (SC-004)

**Goal**: Confirm all 9 rules produce `type="operation"` elements.

**Command**:
```bash
.venv/bin/python3 -c "
from specmetrics.kernel.deterministic_engine import DeterministicSemanticEngine
from specmetrics.kernel.adapter_interface import Document

engine = DeterministicSemanticEngine()

# Test THEN assertion
doc = Document(
    id='test-then',
    content='#### Scenario: Test\n- **THEN** the system displays the panel\n',
    document_type='specification'
)
result = engine.extract([doc])
ops = [e for e in result.elements if e.type == 'operation']
print(f'THEN → operation: {len(ops)} elements')
for o in ops:
    print(f'  type={o.type}, content[:50]={o.content[:50]}')

# Test SHALL statement
doc2 = Document(
    id='test-shall',
    content='The system SHALL process requests within 100ms\n',
    document_type='specification'
)
result2 = engine.extract([doc2])
ops2 = [e for e in result2.elements if e.type == 'operation']
print(f'SHALL → operation: {len(ops2)} elements')

# Test DEVE statement
doc3 = Document(
    id='test-deve',
    content='O sistema DEVE calcular o z-score combinado\n',
    document_type='specification'
)
result3 = engine.extract([doc3])
ops3 = [e for e in result3.elements if e.type == 'operation']
print(f'DEVE → operation: {len(ops3)} elements')

# Test Requirement heading
doc4 = Document(
    id='test-req',
    content='### Requirement: DiagnosisPanel replaces placeholder (DP101)\n',
    document_type='specification'
)
result4 = engine.extract([doc4])
ops4 = [e for e in result4.elements if e.type == 'operation']
print(f'Requirement → operation: {len(ops4)} elements')
print('All rule type changes verified' if all([len(ops)>0,len(ops2)>0,len(ops3)>0,len(ops4)>0]) else 'SOME RULES FAILED')
"
```

**Expected outcome**: All 4 test patterns produce at least 1 operation element.

### 3. Verify Direction Inference (SC-005)

**Goal**: Confirm WHEN clauses get direction "input" and THEN clauses get direction "output".

**Command**:
```bash
.venv/bin/python3 -c "
from specmetrics.kernel.cfm.builder import _infer_operation_direction

# WHEN → input
when_text = '- **WHEN** user clicks the button'
print(f'WHEN direction: {_infer_operation_direction(when_text)} (expected: input)')

# THEN → output
then_text = '- **THEN** the panel SHALL display the result'
print(f'THEN direction: {_infer_operation_direction(then_text)} (expected: output)')

# DEVE → fallback (input)
deve_text = 'O sistema DEVE calcular o z-score combinado'
print(f'DEVE direction: {_infer_operation_direction(deve_text)} (expected: input)')

# Scenario → query
scenario_text = '#### Scenario: User logs in successfully'
print(f'Scenario direction: {_infer_operation_direction(scenario_text)} (expected: query)')
"
```

**Expected outcome**: WHEN → input, THEN → output, DEVE → input, Scenario → query.

### 4. No Regressions Check (SC-006)

**Goal**: Verify that changing fact to operation for 9 rules doesn't break extraction of remaining 23 rules.

**Command**:
```bash
.venv/bin/python3 -c "
from specmetrics.kernel.deterministic_engine import DeterministicSemanticEngine
from specmetrics.kernel.adapter_interface import Document

engine = DeterministicSemanticEngine()
# Load the test samples
import json, glob, os
docs = []
for spec_dir in sorted(glob.glob('tests/openspec/openspec/specs/*')):
    spec_file = os.path.join(spec_dir, 'spec.md')
    if os.path.exists(spec_file):
        with open(spec_file) as f:
            content = f.read()
        docs.append(Document(id=f'os:{os.path.basename(spec_dir)}', content=content, document_type='specification'))

result = engine.extract(docs)
types = {}
for e in result.elements:
    t = e.type
    types[t] = types.get(t, 0) + 1
print(f'Extracted element types: {types}')
print(f'Total elements: {len(result.elements)}')
# Should still have entity and fact types (from unchanged rules)
assert 'entity' in types, 'Entity rules broken!'
print('No regressions: entity rules intact')
"
```

**Expected outcome**: Both `entity` and `fact` types still present alongside new `operation` type.

### 5. Full Pipeline Spot-Check

**Goal**: Run full measure on OpenSpec samples and check all metrics.

**Expected outcomes**:

| Metric | Minimum Expected |
|--------|-----------------|
| Function Points | > 0 |
| Simplified Function Points | > 0 |
| Story Points | > 0 |
| Cognitive Points | > 0 |
| Token Points | > 0 |
