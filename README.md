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
- [Story Points (Modified Fibonacci)](https://framework.scaledagile.com/blog/glossary_term/modified-fibonacci-sequence);
- [T-shirt Sizing](https://asana.com/pt/resources/t-shirt-sizing);
- [Token Points](docs/rfcs/RFC-028%20-%20Token%20Points%20Measurement%20Engine.md);
- [Cognitive Points](docs/rfcs/RFC-029%20-%20Cognitive%20Points%20Measurement%20Engine.md).

> **Note:** The current implementations of **BCP**, **FPA**, **SFP**, and **SNAP** are **draft prototypes** intended solely for demonstration and validation purposes. They provide a highly simplified approximation of their respective measurement methodologies and **do not constitute complete or standards-compliant implementations**. Full conformance with the official specifications requires additional counting rules, validation logic, and methodological details beyond the scope of these prototype implementations.

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

  --metrics, -m: bcp,fpa,sfp,snap,sp,tshirt,tp,cp (comma-separated, defaults to all)
  --export:          Automatically run export after measurement
  --format:          Export format(s) when --export is used (json, csv, xml; comma-separated)

# Full pipeline measurement (all metrics, current path)
specmetrics measure

# Run specific measurements at current path
specmetrics measure --metrics sp,tp,cp

# Run specific stages
specmetrics measure --stage extract
specmetrics measure --from measure

# Measure and export in one command
specmetrics measure --export
specmetrics measure --export --format json,csv

# Output formats
specmetrics measure --output json
specmetrics measure --output json:./results.json

# Verbose or quiet mode
specmetrics measure --verbose
specmetrics measure --quiet

# Plugin management
specmetrics plugins list
specmetrics plugins list --verbose
specmetrics plugins list --type measurement

# Configuration
specmetrics config dump
specmetrics config llm list
specmetrics config llm set deepseek --api-key sk-...
specmetrics config llm show

# Specification validation
specmetrics validate specs/

# Export results
specmetrics export list
specmetrics export run [MEASURE_ID] [PROJECT_PATH] [--format json,csv,xml]
specmetrics export run --format json,csv

# Explain a measurement run
specmetrics explain <run-id>

# Housekeeping: clean old measurement runs
specmetrics clean
specmetrics clean --keep-runs 30 --keep-days 7
specmetrics clean --dry-run

# MCP server (for AI agent integration)
specmetrics mcp start
specmetrics mcp status
specmetrics mcp stop
```

### CLI Parameters

| Command                        | Description                                                                         |
| ------------------------------ | ----------------------------------------------------------------------------------- |
| `clean [options]`              | Remove old measurement run folders from `.specmetrics/runs/` (`--keep-runs`, `--keep-days`, `--dry-run`) |
| `measure [path] [options]`     | Execute full measurement pipeline (`--metrics` to select, `--export` to auto-export) |
| `version`                      | Print platform and plugin versions                                                  |
| `plugins list`                 | List discovered plugins                                                             |
| `plugins verify`               | Verify plugin compatibility                                                         |
| `plugins list-formats`         | List export formats and publishers                                                  |
| `export list`                  | List all measure runs with IDs and timestamps                                       |
| `export run [id] [path]`       | Export measurement results to `.specmetrics/exports/` (JSON, CSV, XML; latest run if no ID; runs pipeline if no runs exist) |
| `export list-formats`          | List exporter plugins                                                               |
| `export publisher-status`      | Show publisher status                                                               |
| `config dump`                  | Show all resolved configuration                                                     |
| `config llm set <provider>`    | Configure LLM provider (chatgpt, gemini, copilot, claude, deepseek, ollama, custom) |
| `config llm list`              | List LLM providers                                                                  |
| `config llm show`              | Show current LLM configuration                                                      |
| `config llm set-model <model>` | Change LLM model                                                                    |
| `config llm set-api-key <key>` | Change LLM API key                                                                  |
| `config llm test`              | Test LLM current provider                                                           |
| `explain <run-id>`             | Explain a measurement result                                                        |
| `mcp start`                    | Start MCP server for AI agents                                                      |
| `mcp stop`                     | Stop MCP server                                                                     |
| `mcp status`                   | Check MCP server status                                                             |
| `validate <paths...>`          | Validate specification documents                                                    |

**Common options across commands:**

| Flag               | Description               |
| ------------------ | ------------------------- |
| `--verbose` / `-v` | Detailed progress output  |
| `--quiet` / `-q`   | Suppress non-error output |
| `--help`           | Show help for any command |

Run `specmetrics --help` or `specmetrics <command> --help` for detailed options on any command.

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

### How to Test (e2e)

```bash
.venv/bin/specmetrics --help
```

---

### Know More

You can find more information [here](docs/PRD.md) and [here](docs/system%20designs/Foundation.md).

All specs can be found [here](specs/).
