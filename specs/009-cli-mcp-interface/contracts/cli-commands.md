# CLI Command Contract

## Command: `specmetrics measure`

Execute the full or partial measurement pipeline.

### Usage

```text
specmetrics measure [OPTIONS] [PROJECT_PATH]
```

### Arguments

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `PROJECT_PATH` | Path | No | `.` | Path to SpecMetrics project |

### Options

| Flag | Type | Description |
|------|------|-------------|
| `--output`, `-o` | Text | Output format and optional path: `json`, `csv`, `xml`, `text`, `json:./path.json` |
| `--stage`, `-s` | Text | Run only this stage: `discover`, `extract`, `graph`, `cfm`, `rule`, `measure`, `export` |
| `--from` | Text | Start from this stage (skip earlier stages) |
| `--verbose`, `-v` | Flag | Detailed per-stage progress |
| `--quiet`, `-q` | Flag | Suppress non-error output |
| `--help` | Flag | Show help and exit |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success — pipeline completed |
| 1 | Error — invalid arguments, missing project, pipeline failure |
| 2 | Plugin error — incompatible or missing plugin |

### Examples

```bash
# Full pipeline, current directory
specmetrics measure

# Full pipeline, explicit project path, JSON output
specmetrics measure --output json ./my-project

# Run only semantic extraction
specmetrics measure --stage extract

# Run from measurement stage onwards
specmetrics measure --from measure

# Quiet mode (CI/CD usage)
specmetrics measure --quiet --output json
```

---

## Command: `specmetrics plugins`

Manage and inspect plugins.

### Usage

```text
specmetrics plugins [COMMAND]
```

### Subcommands

#### `list`

List all discovered plugins.

```text
specmetrics plugins list [OPTIONS]
```

Options:

| Flag | Type | Description |
|------|------|-------------|
| `--verbose`, `-v` | Flag | Show detailed plugin info |
| `--type` | Text | Filter by plugin type (`adapter`, `measurement`, `export`, `publisher`) |

#### `verify`

Verify plugin compatibility.

```text
specmetrics plugins verify
```

### Examples

```bash
specmetrics plugins list
specmetrics plugins list --type measurement
specmetrics plugins verify
```

---

## Command: `specmetrics version`

Display platform and plugin versions.

### Usage

```text
specmetrics version [OPTIONS]
```

### Options

| Flag | Type | Description |
|------|------|-------------|
| `--json` | Flag | Output version info as JSON |

### Example output

```text
SpecMetrics v0.1.0
Python 3.13.3
Plugins:
  openspec v0.1.0 (adapter) ✓
  speckit  v0.1.0 (adapter) ✓
  apf      v0.1.0 (measurement) ✓
```

---

## Command: `specmetrics help`

Display help information.

### Usage

```text
specmetrics help [COMMAND]
```

Shows detailed help for a specific command, or lists all available commands when called without arguments.
