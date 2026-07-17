# Research: Business Complexity Points (BCP) Measurement Engine

## 1. Plugin Architecture

**Decision**: Adapter pattern — `story_generator.py` converts CFM to markdown, `sdk_adapter.py` wraps BCPClient, `plugin.py` orchestrates.

**Rationale**: The BCP plugin is fundamentally different from other measurement plugins (SFP, Story Points, etc.) because it does not implement a scoring algorithm. It converts canonical data into the external SDK's expected format, delegates computation, and maps the response back. Separation of concerns: story generation is independent of SDK invocation, enabling adapter replacement (per FR-021).

**Alternatives considered**: Embedding SDK calls in plugin.py — rejected; mixing story generation + SDK + result mapping in one file violates single responsibility and makes adapter replacement harder.

---

## 2. SDK Integration Strategy

**Decision**: Wrap `BCPClient` in an adapter class (`BcpSdkAdapter`) implementing a plugin-internal protocol. The adapter handles: client instantiation, retry logic, error translation, provider configuration.

**Adapter interface**:
```python
class BcpSdkAdapter:
    def __init__(self, provider: str = "openai", log_level: str = "INFO"): ...
    def calculate(self, story_content: str) -> dict: ...
    def batch_calculate(self, stories: list[str]) -> list[dict]: ...
```

**Retry logic**: `tenacity` library or manual exponential backoff. Per-item retry with 3 attempts (1s, 2s, 4s delays). Transient failures (timeout, rate limit, 5xx) trigger retry; auth failures (4xx) fail immediately.

**Provider config**: Read from Rule Pack or environment. Default to `"openai"`.

**Alternatives considered**: Direct BCPClient usage without wrapper — rejected because retry logic, error translation, and logging would be scattered across the handler. Protocol-based adapter enables SDK replacement (per clarification).

---

## 3. Story Generation Format

**Decision**: Template-based markdown generation from CFM element attributes. Each FunctionalProcess produces a markdown string.

**Template**:
```markdown
# User Story: {functional_process.name}

As a {actor_names}, I want to {functional_process.description}

## Acceptance Criteria:
{operations → bullet list}
{business_rules → bullet list}
{data_groups → bullet list}
{relationships → bullet list}
```

**Fields populated from CFM**:
- `functional_process.name` → story title
- `functional_process.actor_ids` → resolve actor names from `cfm.actors`
- `functional_process.operation_ids` → resolve from `cfm.operations`
- `functional_process.data_group_ids` → resolve from `cfm.data_groups`
- `cfm.business_rules` filtered by `related_process_ids` → rule descriptions
- `cfm.relationships` filtered by source/target → relationship descriptions

**Alternatives considered**: Raw JSON serialization — rejected because SDK's `calculate()` expects markdown string, not JSON.

---

## 4. Pipeline Integration

**Decision**: BCP handler subscribes to `EventType.MEASUREMENT_COMPLETED` (same event as other measurement plugins). Reads CFM from `ctx.canonical_model`.

**Rationale**: Consistent with all existing measurement plugins. BCP does not need a separate event because it runs independently alongside SFP, Story Points, etc. (organization selects which measurement method to run).

**Handler flow**:
1. Read CFM from `ctx.canonical_model`
2. If None → return empty result with warnings (graceful degradation)
3. For each Functional Process: generate story → call SDK via adapter → collect result
4. Build per-item BCPWorkItem list with story + SDK response
5. Compute total_bcp from sum of item scores
6. Write `ctx.with_stage_output("measurement_result", payload)`

---

## 5. Error Handling & Retry

**Decision**: Per-item retry with exponential backoff (3 attempts). Skip failed items and continue batch.

**Error categories**:

| Category | Examples | Action |
|----------|----------|--------|
| Transient | Timeout, rate limit, 5xx | Retry (3 attempts, exponential backoff 1s/2s/4s) |
| Auth | Invalid API key, 401, 403 | Fail immediately, abort measurement |
| Input | Empty story, malformed request | Skip item with warning |
| SDK unavailability | Import error, missing dependency | Return empty result with warnings |

**Partial batch failure**: Record failed items in `warnings` with SDK error details. Items that succeed are included in the result. `total_bcp` reflects only successful items.

---

## 6. Environment & Credentials

**Decision**: The SDK loads credentials from `.env` via `python-dotenv`. The plugin validates credential presence before SDK calls and emits clear error messages if missing.

**Required env vars**: `OPENAI_API_KEY` (for OpenAI provider), `ANTHROPIC_API_KEY` (for Claude provider).

**Validation**: On plugin init, check if the configured provider's env var is set. If missing, emit warning and skip SDK call (empty result).

---

## 7. Import Path Handling

**Decision**: The SDK may be installed as `bcp-calculator` (published package) or from a local `bcp-agent` directory (via `pip install -e .`). The plugin tries both import paths:

```python
try:
    from bcp_calculator import BCPClient
except ImportError:
    try:
        from src.sdk import BCPClient
    except ImportError:
        raise ImportError("bcp-calculator SDK not installed")
```

**Alternatives considered**: Requiring a single import path — rejected because the SDK may be installed in either form depending on the organization's setup.
