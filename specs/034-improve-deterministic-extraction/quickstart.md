# Quickstart: Validating Deterministic Extraction Improvements

**Feature**: 034-improve-deterministic-extraction

## Prerequisites

- Python 3.12+ virtual environment with `specmetrics` installed (`pip install -e .`)
- No LLM API key configured (forces deterministic fallback)
- The SpecMetrics project itself as the test target (contains SpecKit specifications with GWT scenarios)

## Validation Scenarios

### 1. Verify Operation Extraction (US1, P1)

**Goal**: Confirm the deterministic engine produces operation elements from GWT patterns.

**Command**:
```bash
.venv/bin/specmetrics measure
```

**Expected outcome**:
- `specmetrics measure` completes without errors
- The CFM contains at least 1 functional process (previously 0)
- Story Points measurement returns a non-zero total
- FPA results include transactional function types (EI, EO, EQ) in addition to ILF

**Verification**:
```bash
# Check CFM for functional processes
python3 -c "
import json
with open('.specmetrics/runs/$(ls -t .specmetrics/runs/ | head -1)/cfm.json') as f:
    data = json.load(f)
types = {}
for e in data[0]['entities']:
    t = e.get('type', 'unknown')
    types[t] = types.get(t, 0) + 1
print('CFM types:', types)
# Should show functional_process > 0 and operation > 0
"
```

### 2. Verify SNAP Semantic Markers (US2, P2)

**Goal**: Confirm CFM elements have `semantic_marker` metadata and SNAP produces classified items.

**Command**:
```bash
# Check SNAP results
python3 -c "
import json
with open('.specmetrics/runs/$(ls -t .specmetrics/runs/ | head -1)/measure.json') as f:
    data = json.load(f)
for e in data[0]['entities']:
    if e['metric'] == 'snap':
        print(f'SNAP total items: {e[\"total\"]}')
        # Should be > 0
        break
"
```

**Expected outcome**: SNAP `total` > 0 (previously 0 with 1005 warnings).

### 3. Verify Actor Identification (US3, P3)

**Goal**: Confirm some entities are correctly classified as actors.

**Command**:
```bash
python3 -c "
import json
with open('.specmetrics/runs/$(ls -t .specmetrics/runs/ | head -1)/cfm.json') as f:
    data = json.load(f)
actors = [e for e in data[0]['entities'] if e.get('type') == 'actor']
print(f'Actors found: {len(actors)}')
for a in actors[:3]:
    print(f'  - {a[\"name\"][:60]}')
"
```

**Expected outcome**: At least 1 actor element (previously 0).

### 4. Full Pipeline Spot-Check

**Goal**: Run the full pipeline and verify no regressions.

**Command**:
```bash
.venv/bin/specmetrics measure
```

**Expected outcomes**:

| Metric | Before | After (minimum) |
|--------|--------|-----------------|
| Function Points | 434 | >= 434 (may increase with transactional functions) |
| Simplified Function Points | 62 | >= 62 |
| Story Points | 0 | > 0 |
| SNAP | 0 | > 0 |
| Token Points | ~4238 | ~4238 (no regression) |
| Cognitive Points | 100 | ~100 (no regression) |
| BCP | 0 | 0 (SDK-dependent) |
| TShirt | 0 | 0 (depends on Story Points) |

### 5. Evidence Traceability Check

**Goal**: Verify all new elements maintain evidence references.

**Command**:
```bash
python3 -c "
import json
with open('.specmetrics/runs/$(ls -t .specmetrics/runs/ | head -1)/cfm.json') as f:
    data = json.load(f)
broken = []
for e in data[0]['entities']:
    ev = e.get('evidence', {})
    if not ev or not ev.get('graph_node_id') or not ev.get('document_id'):
        broken.append(e.get('id', 'unknown'))
if broken:
    print(f'BROKEN EVIDENCE: {len(broken)} elements')
else:
    print('All elements have valid evidence references')
"
```

**Expected outcome**: Zero broken evidence references.

### Edge Case Validation

```bash
# Test with a single spec file containing GWT scenarios
.venv/bin/python3 -c "
from pathlib import Path
from specmetrics.kernel.deterministic_engine import DeterministicSemanticEngine
from specmetrics.kernel.adapter_interface import Document

engine = DeterministicSemanticEngine()
doc = Document(
    id='test-gwt',
    content='''
## User Story 1

**GIVEN** a user is logged in
**WHEN** they click submit
**THEN** the form is saved
''',
    document_type='speckit:specification'
)
result = engine.extract([doc])
ops = [e for e in result.elements if e.type == 'operation']
print(f'Operations extracted: {len(ops)}')
for op in ops:
    print(f'  type={op.type}, content={op.content[:60]}...')
"
```
**Expected**: At least 3 operations detected (one per GWT line).
