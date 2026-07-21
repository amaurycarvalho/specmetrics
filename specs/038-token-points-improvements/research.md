# Research: Token Points Improvements

**Feature**: 038-token-points-improvements
**Date**: 2026-07-21

## Research Task 1: Content Text Sources per CSM/CFM Element Type

### Finding

Each element type in the canonical models has a specific attribute for its text content:

**CSM elements:**
| Collection | Content source |
|------------|---------------|
| SpecificationActivity | `description` (str) |
| Decision | `description` (str) |
| Assumption | `description` (str) |
| Constraint | `description` (str) |
| Risk | `description` (str) |
| OpenQuestion | `description` (str) |
| AcceptanceCriterion | `description` (str) |
| GlossaryTerm | `description` (str) |
| References | `url` + `title` (no description field) |

**CFM elements:**
| Collection | Content source |
|------------|---------------|
| FunctionalProcess | `name` + `description` |
| BusinessRule | `name` + `description` |
| Operation | `name` + `description` |
| DataGroup | `name` + `description` |
| Relationship | `name` (no description; stored as list) |
| Actor | `name` + `description` |

### Decision

Content token count = tokens(name + " " + description) for elements with descriptions. For relationships and other elements with only a name: tokens(name). For references: tokens(title + " " + url). The concatenation approach is simple and matches how an LLM would consume these fields (as part of structured system prompts).

### Alternatives Considered

- **Tokenize only description**: Rejected — element names carry semantic weight and appear in prompts.
- **Weight different fields differently**: Over-engineering for v1; can be added via calibration later.

---

## Research Task 2: tiktoken Integration Strategy

### Finding

tiktoken is the standard OpenAI tokenizer library. It provides `tiktoken.get_encoding("cl100k_base")` for GPT-4/GPT-3.5 token counting. The library is pure Python, fast (~1M tokens/sec), and widely available.

However, making it a hard dependency adds installation complexity for users who only use deterministic extraction or non-OpenAI providers.

### Decision

Lazy import with fallback:
```python
try:
    import tiktoken
    _enc = tiktoken.get_encoding("cl100k_base")
    def count_tokens(text: str) -> int:
        return len(_enc.encode(text))
except ImportError:
    def count_tokens(text: str) -> int:
        return max(1, len(text) // 4)
```

The fallback uses the standard 4 chars ≈ 1 token heuristic. A warning is logged once per engine initialization if tiktoken is not available.

### Alternatives Considered

- **Hard dependency on tiktoken**: Rejected — unnecessary for users not using OpenAI providers.
- **Character count only (no tiktoken)**: Rejected — tiktoken produces exact results and is easy to install.
- **Configurable tokenizer choice**: Deferred to future (not needed for v1).

---

## Research Task 3: Calibration Profile Defaults

### Finding

The current `SpecificationCostWeights` model (`calibration/models.py` line 6-14) has:
```python
class SpecificationCostWeights(BaseModel):
    activities: dict[str, float] = Field(default_factory=dict)  # empty!
    decisions: float = 1.5
    assumptions: float = 1.0
    constraints: float = 1.5
    risks: float = 2.0
    open_questions: float = 1.0
    acceptance_criteria: float = 1.0
    glossary_terms: float = 0.5
```

The `activities` dict is empty by default, meaning all activity types produce 0.0 unless a YAML overrides them. References are not even a field — they're ignored entirely.

### Decision

Update defaults to:
```python
activities: dict[str, float] = Field(default_factory=lambda: {
    "exploration": 2.0,
    "clarification": 3.0,
    "refinement": 3.0,
    "review": 1.5,
    "validation": 2.0,
})
references: float = 1.0
```

Add `content_multiplier: float = 0.1` to `CalibrationProfile`. The weight rationales: clarification and refinement are more token-intensive (involve back-and-forth discussion), while review is lighter (checklist-style verification).

### Alternatives Considered

- **Different weight values**: The specific values (2.0, 3.0, etc.) were chosen to be roughly proportional to the expected relative token cost of each activity type based on common specification patterns. Users can override via YAML.
- **Auto-calibrate from historical data**: Deferred to future — requires usage telemetry infrastructure.

---

## Research Task 4: Score Formula Impact on Existing Values

### Finding

The current approach produces Token Points in the range of 10-200 for typical projects. With content-based estimation, the same project could produce scores 2-5x higher (depending on description verbosity).

For example, a project with 3 functional processes (type weight = 5.0 each) currently scores 15.0 for those processes. With content-based estimation, if each process has a 200-token description, the content contribution adds 200 × 0.1 = 20.0 per process, making the total 3 × (5.0 + 20.0) = 75.0 — a 5x increase.

### Decision

This increase is intentional and documented. The old flat-weight values were arbitrary and not comparable across projects. The new values are grounded in content volume and are comparable. The spec's SC-001 validates this: a 2:1 content ratio should produce a 1.5:1 to 2.5:1 score ratio.

Organizations that have calibrated their Kanban processes around the old flat-weight values will need to re-calibrate. The `content_multiplier` can be set to 0.0 to revert to flat-weight-only behavior.

### Alternatives Considered

- **Normalize scores to old range**: Rejected — defeats the purpose of content grounding.
- **Version the calibration format with migration**: Over-engineering; the defaults change is backward-compatible (old YAML files load correctly with new model defaults).
