# RFC-030 — Semantic Extraction Engine

**RFC**: 030

**Title**: Semantic Extraction Engine

**Status**: Draft

**Author**: SpecMetrics Team

**Created**: 2026-07-17

**Related Specification**: F27 – Semantic Extraction Engine

---

# Summary

This RFC introduces the **Semantic Extraction Engine**, a unified abstraction responsible for transforming normalized specification documents into canonical semantic elements.

The Semantic Extraction Engine decouples the measurement pipeline from any specific semantic extraction strategy, allowing deterministic and LLM-assisted implementations to coexist behind a common interface.

---

# Motivation

Earlier versions of SpecMetrics assumed semantic extraction was always performed by an LLM.

This created unnecessary coupling between the pipeline and AI providers.

The platform now supports:

- deterministic extraction
- LiteLLM-backed extraction
- future extraction strategies

without changing the pipeline.

---

# Goals

- Provide a single semantic extraction abstraction.
- Decouple pipeline stages from extraction implementations.
- Support execution with or without LLMs.
- Keep CLI and MCP configuration simple.
- Preserve deterministic pipeline behavior.

---

# Non-Goals

This RFC does not define:

- AST parsing
- heuristic rules
- prompt engineering
- semantic extraction algorithms

Those belong to RFC-031.

---

# Architecture

```
Pipeline
      │
      ▼
SemanticEngineFactory
      │
      ▼
SemanticExtractionEngine
      │
      ├── DeterministicSemanticEngine
      └── LiteLLMSemanticEngine
```

Only the factory knows which implementation is instantiated.

---

# Public Configuration

The public configuration remains centered on LLM providers.

Examples:

```bash
specmetrics config llm set none

specmetrics config llm set chatgpt

specmetrics config llm set claude

specmetrics config llm set ollama
```

Users never configure semantic engines directly.

---

# Engine Resolution

| Provider | Engine                      |
| -------- | --------------------------- |
| none     | DeterministicSemanticEngine |
| chatgpt  | LiteLLMSemanticEngine       |
| claude   | LiteLLMSemanticEngine       |
| gemini   | LiteLLMSemanticEngine       |
| ollama   | LiteLLMSemanticEngine       |

This mapping is internal.

---

# Semantic Engine Interface

Every implementation exposes the same contract.

Example:

```python
class SemanticExtractionEngine(Protocol):

    def extract(
        self,
        documents: list[Document]
    ) -> ExtractionResult:
        ...
```

---

# Responsibilities

The engine is responsible for:

- semantic extraction
- evidence preservation
- confidence generation
- extraction statistics
- deterministic output model

The engine is **not** responsible for:

- provider configuration
- pipeline orchestration
- graph construction

---

# CLI Compatibility

No CLI changes are introduced.

Current commands remain valid.

```bash
specmetrics config llm set none

specmetrics config llm set chatgpt
```

---

# MCP Compatibility

The MCP API mirrors the CLI behavior.

Clients configure providers.

They never configure engines.

---

# Factory

The factory resolves the implementation.

Example:

```python
if provider == "none":
    return DeterministicSemanticEngine()

return LiteLLMSemanticEngine(...)
```

---

# Design Principles

- Strategy Pattern
- Dependency Inversion
- Open/Closed Principle
- Layer Independence
- Deterministic Interfaces

---

# Future Extensions

Possible future implementations:

- CachedSemanticEngine
- MCPSemanticEngine
- HybridSemanticEngine
- RemoteSemanticEngine

No pipeline changes are required.

---

# Benefits

- Stable public API
- Internal implementation flexibility
- Simple configuration
- Offline support
- Testability
- Extensibility

---

# Backward Compatibility

Fully backward compatible.

No CLI, MCP or plugin changes are required.
