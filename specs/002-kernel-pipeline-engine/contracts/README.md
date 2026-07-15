# Contracts: Kernel & Pipeline Engine

This directory defines the public interfaces (contracts) that the Pipeline Engine
exposes to plugin developers and other kernel components. All contracts are
framework-agnostic protocol definitions.

## Contract Overview

| Contract | Purpose | Implemented By |
|----------|---------|----------------|
| [EventHandler](event-handler.md) | Interface for pipeline stage handlers | All pipeline stage plugins |
| [PipelineEvents](pipeline-events.md) | Event type catalog and payload schemas | Pipeline Engine + all stages |
| [PipelineContext](pipeline-context.md) | Execution state container interface | Pipeline Engine |

## Design Rules

1. All contracts use only Python stdlib type hints — no framework coupling
2. Handlers communicate exclusively through events — no direct calls
3. Each event type maps to exactly one handler
4. Contracts are versioned via the event type enum — adding a new event type
   is a backward-compatible change
