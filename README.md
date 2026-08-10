# SpecMetrics

A Functional Measurement Engine for Spec Driven Development (SDD)

[![Spec-Driven Development](https://img.shields.io/badge/SDD-SpecKit-yellow)](.specify/memory/constitution.md)

---

## Vision

**SpecMetrics** is an Open Source **Functional Measurement Engine** for **Specification Driven Development (SDD)**.

Its purpose is to transform software specifications into structured, traceable and measurable engineering assets, enabling deterministic functional measurement directly from specification artifacts instead of source code or manually interpreted requirements.

SpecMetrics leverages Large Language Models to semantically understand specifications produced by frameworks such as OpenSpec and SpecKit, extracting evidence-based functional knowledge that is normalized into a canonical internal representation. This representation is then consumed by deterministic measurement engines capable of applying different functional sizing methodologies while preserving traceability and explainability.

Beyond functional measurement, SpecMetrics provides a foundation for engineering observability by exposing structured functional information that can be consumed by dashboards, DevOps platforms, software quality tools and AI-assisted development workflows through an extensible plugin ecosystem.

## How it Works

### Input Specs

- [OpenSpec](https://github.com/Fission-AI/openspec);
- [SpecKit](https://github.com/github/spec-kit).

### Evaluate Metrics

- [Function Point Analysis (IFPUG/FPA)](https://ifpug.org/ifpug-standards/fpa);
- [Simplified Function Point (IFPUG/SFP)](https://ifpug.org/ifpug-standards/sfp);
- [Software Non-Functional Assessment Process (IFPUG/SNAP)](https://ifpug.org/ifpug-standards/snap);
- [Business Complexity Points (CI&T/Itaú/BCP)](https://ciandt.com/us/en-us/complexitypoints)
- [Story Points (Modified Fibonacci)](docs/rfcs/RFC-041%20-%20Story%20Points%20Measurement%20Engine.md);
- [T-shirt Sizing](docs/rfcs/RFC-042%20-%20T-Shirt%20Sizing.md);
- [Token Points](docs/rfcs/RFC-028%20-%20Token%20Points%20Measurement%20Engine.md);
- [Cognitive Points](docs/rfcs/RFC-029%20-%20Cognitive%20Points%20Measurement%20Engine.md).

> **Note:**
>
> 1. The current implementations of **BCP**, **FPA**, **SFP**, and **SNAP** are **draft prototypes** intended solely for demonstration and validation purposes. They provide a highly simplified approximation of their respective measurement methodologies and **do not constitute complete or standards-compliant implementations**. Full conformance with the official specifications requires additional counting rules, validation logic, and methodological details beyond the scope of these prototype implementations;
> 2. **BCP** support requires SDK installed (`pip install bcp-calculator`);
> 3. **LLM** support requires LiteLLM installed (`pip install litellm`).

### Output Formats

- JSON
- CSV
- XML
- Markdown

---

## 🧑‍💻 For Users

### How to Install

Download the wheel from [Releases](https://github.com/amaurycarvalho/specmetrics/releases).

After, use the command below to install it.

```bash
uv tool install specmetrics-<version>-py3-none-any.whl
```

or

```bash
pipx install --force specmetrics-<version>-py3-none-any.whl
```

### Setting Up

Before running measurements, configure the LLM provider for semantic extraction:

```bash
# List available providers
specmetrics config llm list

# Configure a simple deterministic local provider as LLM (default)
specmetrics config llm set none

# Configure a provider (e.g., ChatGPT/OpenAI)
specmetrics config llm set chatgpt --api-key sk-...

# Use a different model
specmetrics config llm set openai --model gpt-4o --api-key sk-...

# Test LLM connection
specmetrics config llm test

# Or use environment variables
export SPECMETRICS_LLM_API_KEY=sk-...
```

> **Note**: LLM configuration is stored in `~/.config/specmetrics/config.yml`, outside your project directory. If no API key is configured, the pipeline falls back to structural extraction.

### How to Use

```bash
# Measurement syntax
specmetrics measure [PROJECT_PATH] [OPTIONS]
```

### CLI Reference

Run `specmetrics --help` or `specmetrics <command> --help` for detailed options on any command.

#### Global Flags

| Flag               | Description               |
| ------------------ | ------------------------- |
| `--verbose` / `-v` | Detailed progress output  |
| `--quiet` / `-q`   | Suppress non-error output |
| `--help`           | Show help for any command |

#### `specmetrics measure`

Execute the full measurement pipeline on a specification project.

```bash
specmetrics measure [PATH] [OPTIONS]
```

| Parameter          | Type       | Default | Description                                                                                      |
| ------------------ | ---------- | ------- | ------------------------------------------------------------------------------------------------ |
| `PATH`             | positional | `"."`   | Path to the SpecMetrics project                                                                  |
| `--metrics`, `-m`  | str        | all     | Comma-separated: `bcp,fpa,sfp,snap,sp,tshirt,tp,cp`                                              |
| `--output`, `-o`   | str        | text    | Format: `json`, `csv`, `xml`, `text`, or `json:./path.json`                                      |
| `--stage`, `-s`    | str        | —       | Run only this stage: `discover`, `extract`, `graph`, `cfm`, `rule`, `measure`, `export`          |
| `--from`           | str        | —       | Start from this stage: `discover`, `extract`, `graph`, `csm`, `cfm`, `rule`, `measure`, `export` |
| `--export`         | flag       | off     | Auto-export after measurement                                                                    |
| `--format`         | str        | json    | Export format(s) when `--export` is used: `json,csv,xml`                                         |
| `--log-file`, `-l` | str        | —       | Persist logs to `.specmetrics/logs/<filename>`                                                   |
| `--llm-rpm-limit`  | int        | 15      | LLM requests per minute limit (0 = unlimited)                                                    |
| `--config`, `-c`   | path       | —       | Path to configuration file (supports `$ENV_VAR` expansion)                                       |
| `--verbose`, `-v`  | flag       | off     | Show detailed per-stage progress                                                                 |
| `--quiet`, `-q`    | flag       | off     | Suppress non-error output                                                                        |

Examples:

```bash
specmetrics measure                                          # All metrics, current path
specmetrics measure --metrics sp,tp,cp                       # Specific metrics
specmetrics measure --stage extract                          # Single stage
specmetrics measure --from measure                           # Skip to measurement
specmetrics measure --export --format json,csv               # Measure and export
specmetrics measure --llm-rpm-limit 10                       # Limit LLM calls
specmetrics measure --output json:./results.json             # Output to file
specmetrics measure --verbose                                # Detailed output
```

> **Note**: Measure detailed results is stored in `.specmetrics/runs/{measure id}/`.

#### `specmetrics clean`

Remove old measurement run folders.

```bash
specmetrics clean [OPTIONS]
```

| Parameter         | Type | Default | Description                            |
| ----------------- | ---- | ------- | -------------------------------------- |
| `--project-path`  | path | `"."`   | Path to the SpecMetrics project        |
| `--keep-runs`     | int  | 90      | Max recent runs to retain (0 disables) |
| `--keep-days`     | int  | 30      | Max age in days (0 disables)           |
| `--dry-run`       | flag | off     | Preview without deleting               |
| `--verbose`, `-v` | flag | off     | Detailed progress output               |
| `--quiet`, `-q`   | flag | off     | Suppress non-error output              |

#### `specmetrics version`

Print platform version, Python version, and discovered plugins.

```bash
specmetrics version
```

#### `specmetrics plugins`

Manage and inspect plugins.

| Subcommand     | Description                                                                                             |
| -------------- | ------------------------------------------------------------------------------------------------------- |
| `list`         | List discovered plugins (`--type` filter: `adapter`, `measurement`, `export`, `publisher`; `--verbose`) |
| `verify`       | Check all discovered plugins for compatibility                                                          |
| `list-formats` | List discovered export formats and publishers                                                           |

#### `specmetrics export`

Export measurement results to various formats.

| Subcommand                | Description                                                                              |
| ------------------------- | ---------------------------------------------------------------------------------------- |
| `run [id] [path]`         | Export results (`--format json,csv,xml`; `--output-dir`; `--publish`; `--otel-endpoint`) |
| `list [path]`             | List all measure runs with IDs and timestamps                                            |
| `list-formats`            | List available exporter plugins                                                          |
| `publisher-status [path]` | Show publisher connection state and metrics                                              |

#### `specmetrics config`

Inspect and manage configuration.

| Subcommand              | Description                                                                                                                                |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `dump`                  | Show all resolved configuration (`--format text\|json`)                                                                                    |
| `llm list`              | List all available LLM providers                                                                                                           |
| `llm set <provider>`    | Configure provider: `chatgpt`, `gemini`, `copilot`, `claude`, `deepseek`, `ollama`, `none`, `custom` (`--model`, `--api-key`, `--api-url`) |
| `llm show`              | Show current LLM configuration                                                                                                             |
| `llm set-model <model>` | Change LLM model                                                                                                                           |
| `llm set-api-key <key>` | Change LLM API key                                                                                                                         |
| `llm test`              | Test LLM connection                                                                                                                        |

#### `specmetrics explain`

Explain a measurement result with evidence traces and rule effects.

```bash
specmetrics explain <run-id> [OPTIONS]
```

| Parameter   | Description                                  |
| ----------- | -------------------------------------------- |
| `run-id`    | Identifier of the measurement run (required) |
| `--metric`  | Specific metric to explain                   |
| `--format`  | Output format: `text` or `json`              |
| `--compare` | Compare with another run ID                  |
| `--run-dir` | Directory containing run artifacts           |

#### `specmetrics mcp`

Manage the SpecMetrics MCP server for AI agent integration.

| Subcommand | Description                                                                                                     |
| ---------- | --------------------------------------------------------------------------------------------------------------- |
| `start`    | Start MCP server (`--host`, `--port`, `--transport stdio\|sse`, `--max-connections`, `--log-level`, `--config`) |
| `stop`     | Stop MCP server (`--timeout` seconds)                                                                           |
| `status`   | Show MCP server status (PID, uptime)                                                                            |

#### `specmetrics validate`

Validate specification documents for correctness and compliance.

```bash
specmetrics validate <paths...> [OPTIONS]
```

| Parameter             | Description                                       |
| --------------------- | ------------------------------------------------- |
| `paths...`            | Specification file(s) or director(ies) (required) |
| `--rules`             | Path to custom validation rules configuration     |
| `--format`            | Output format: `text`, `json`, `quiet`            |
| `--batch`             | Treat paths as a batch                            |
| `--constitution-only` | Only run constitutional compliance checks         |
| `--structural-only`   | Only run structural checks                        |

---

## 👨‍🔧 For Developers

### How to Get the Source Code

```bash
git clone https://github.com/amaurycarvalho/specmetrics.git
```

### How to Build

```bash
make build
```

#### Linting and Unit Testing

```bash
make lint test
```

#### Quality Gate

The quality gate enforces complexity, duplication, coverage, mutation and
security thresholds (RFC-043). Run it locally with:

```bash
make quality-gate
```

Individual checks: `make complexity`, `make duplication`, `make mutation`,
`make security`. See [Quality Gate](docs/adrs/ADR-002%20-%20Quality%20Gate.md) for thresholds and the
exception process.

### Mutation testing

Make sure everything is installed.

```bash
make install-quality-tools
```

Run it locally (it can be time-consuming and require significant processing).

```bash
make mutation-run
```

Then, generate the results report and use it with your AI agent to fix your unit tests.

```bash
make mutation-results
```

Finally, run the mutation testing again and check if it pass the quality gate.

### How to Test (e2e)

```bash
.venv/bin/specmetrics --help
```

---

### Know More

You can find more information [here](docs/PRD.md), [here](docs/adrs/ADR-001%20-%20SpecMetrics.md) and [here](docs/system%20designs/Foundation.md).

All specs can be found [here](specs/).
