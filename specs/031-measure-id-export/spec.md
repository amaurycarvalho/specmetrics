# Feature Specification: Measure ID & Export Commands

**Feature Branch**: `031-measure-id-export`

**Created**: 2026-07-20

**Status**: Draft

**Input**: User description: "Cada rodada do comando `measure` deverá gerar um `measure-id` e seus resultados gravados em uma subpasta .specmetrics/runs/<measure-id>/ em formato json. O formato de gravação do json é o mesmo usado pelo `export run`. No output do comando em tela deverá ser informado o id criado para essa rodada. Deverá ser registrado tambem na tag measure.id antes de measure.sdd_framework em specmetrics-output.json. Registre também a tag measure.id_path contendo o nome da pasta do measure id. Se for informado a option `--export`, um `export run` deverá ser rodado ao final do `measure`. Nesse caso, se tiver também a option `--format json,csv,xml`, ela deverá ser respeitada pelo `export run`. Se não for informado o `--format`, o default é o mesmo do `export run`. Crie o comando `export list` para listar os ids de measure disponíveis. O comando `export run` deverá exportar as informações de um determinado id de measure. O default é o último rodado. Se o id informado não existir ou não houver o ultimo rodado, informará ao usuário que precisa rodar o measure (se não existir nenhum) ou que o id indicado não existe. Deverá ser exportado para a pasta exports/ um arquivo para cada stage. Cada arquivo deverá conter o que foi identificado no stage relacionado, isto é, se o stage identificou "documents" será exportado os nomes dos documentos identificados e paths relativos. Se for "items", será exportado esses items e seus conteudos. Se for "metrics", será as metricas e seus resultados. Se `--format` não for informado, o default é json. No cenário de export de json, a tarefa é apenas copiar os arquivos contidos na pasta do id do measure em .specmetrics/runs/<measure-id>/ para a pasta exports/. No cenário de export em csv ou xml, uma conversão deverá ser feita. Atualize README.md com as sintaxes envolvidas nessa spec."

## User Scenarios & Testing

### User Story 1 — Run Measure and Capture Run ID (Priority: P1)

A quality engineer runs `specmetrics measure` on their project. The command executes the measurement pipeline and outputs a unique measure ID (e.g., `abc123-def456`) to the terminal. Results are persisted to `.specmetrics/runs/<measure-id>/` as a JSON file. The existing `specmetrics-output.json` is also updated to include the `measure.id` and `measure.id_path` tags.

**Why this priority**: This is the core new behavior — every measure run must produce an identifiable, persisted result. All downstream features (export list, export run) depend on this.

**Independent Test**: Can be fully tested by running `specmetrics measure` on a known test project and verifying (a) a non-empty measure ID is printed, (b) `.specmetrics/runs/<measure-id>/` contains the JSON output, and (c) `specmetrics-output.json` includes `measure.id` and `measure.id_path`.

**Acceptance Scenarios**:

1. **Given** a valid project, **When** the user runs `specmetrics measure`, **Then** the CLI prints a message like `Measure ID: <id>` with a unique identifier
2. **Given** a valid project, **When** the user runs `specmetrics measure`, **Then** a folder `.specmetrics/runs/<measure-id>/` is created containing the JSON result file(s)
3. **Given** a valid project, **When** the user runs `specmetrics measure`, **Then** the file `.specmetrics/output/specmetrics-output.json` includes a `measure.id` field (before `measure.sdd_framework`) and a `measure.id_path` field

---

### User Story 2 — Run Measure with Automatic Export (Priority: P1)

A quality engineer runs `specmetrics measure --export` to both measure and export results in one step. After the measurement completes, the export run executes automatically using the newly generated measure ID. If `--format csv` is also provided, the export uses that format.

**Why this priority**: This saves a manual step for users who want measurement results exported immediately. The `--export` flag integrates the two commands into a single workflow.

**Independent Test**: Can be tested by running `specmetrics measure --export` and verifying that (a) the measure completes, (b) an export run is automatically triggered, and (c) export files appear in the `exports/` directory.

**Acceptance Scenarios**:

1. **Given** a valid project, **When** the user runs `specmetrics measure --export`, **Then** after the measure completes, an `export run` is automatically executed using the same measure ID
2. **Given** a valid project, **When** the user runs `specmetrics measure --export --format csv`, **Then** the automatic export uses the CSV format
3. **Given** a valid project, **When** the user runs `specmetrics measure --export --format json,xml`, **Then** the automatic export uses the specified formats
4. **Given** a valid project, **When** the user runs `specmetrics measure --export` without `--format`, **Then** the automatic export uses the default format (json)

---

### User Story 3 — List Available Measure Runs (Priority: P1)

A quality engineer runs `specmetrics export list` to see all past measure runs. The command lists each available measure ID along with its creation timestamp, ordered from most recent to oldest.

**Why this priority**: Users need to discover which measure runs are available before they can export a specific one. This is a prerequisite for the `export run` command's usability.

**Independent Test**: Can be tested by running `specmetrics measure` twice, then `specmetrics export list`, and verifying both measure IDs appear in the output.

**Acceptance Scenarios**:

1. **Given** one or more previous measure runs, **When** the user runs `specmetrics export list`, **Then** all measure IDs are listed, ordered by recency
2. **Given** no previous measure runs, **When** the user runs `specmetrics export list`, **Then** a message like "No measure runs found" is displayed
3. **Given** the list of runs, **When** displayed, **Then** each entry shows the measure ID and its creation timestamp

---

### User Story 4 — Export a Specific Measure Run (Priority: P1)

A quality engineer runs `specmetrics export run <measure-id>` to generate export files for a specific previous measurement. Files are written to the `exports/` directory, with one file per pipeline stage.

**Why this priority**: The primary export use case — retrieve structured results from a past measurement without re-running the pipeline.

**Independent Test**: Can be tested by running `specmetrics measure`, then `specmetrics export run <measure-id>`, and verifying that `exports/` contains per-stage files with the correct content.

**Acceptance Scenarios**:

1. **Given** an existing measure run with ID `<id>`, **When** the user runs `specmetrics export run <id>`, **Then** the `exports/` directory contains one file per pipeline stage (e.g., `discover.json`, `extract.json`, `measure.json`)
2. **Given** an existing measure run, **When** the user runs `specmetrics export run <id> --format csv`, **Then** the `exports/` directory contains CSV files (one per stage) with converted content
3. **Given** an existing measure run, **When** the user runs `specmetrics export run <id> --format xml`, **Then** the `exports/` directory contains XML files (one per stage) with converted content

---

### User Story 5 — Export Latest Measure Run (Default) (Priority: P1)

A quality engineer runs `specmetrics export run` without specifying a measure ID. The command automatically selects the most recent measure run and exports its results. This is the most common export workflow for users who just finished a measurement.

**Why this priority**: Convenience — users should not need to look up and type an ID when they want to export the most recent results.

**Independent Test**: Can be tested by running `specmetrics measure`, then `specmetrics export run`, and verifying the latest measure ID is used.

**Acceptance Scenarios**:

1. **Given** at least one measure run exists, **When** the user runs `specmetrics export run`, **Then** the command uses the most recent measure run
2. **Given** an existing latest measure, **When** exported, **Then** the files in `exports/` match that run's data

---

### User Story 6 — Error Handling and Fallback for Missing Export Runs (Priority: P2)

A user runs `specmetrics export run <nonexistent-id>` and receives a clear error message indicating the ID was not found. A user runs `specmetrics export run` when no runs exist and the command falls back to running the measurement pipeline directly (backward compatible behavior).

**Why this priority**: Defensive error handling ensures users understand what went wrong without consulting documentation.

**Independent Test**: Can be tested by running `specmetrics export run nonexistent-id` on a fresh project with no runs, and verifying the error message.

**Acceptance Scenarios**:

 1. **Given** no previous measure runs exist, **When** the user runs `specmetrics export run`, **Then** the command falls back to running the pipeline directly (backward compatible behavior)
2. **Given** no measure run with the given ID exists, **When** the user runs `specmetrics export run <id>`, **Then** a message is shown: "Measure run `<id>` not found."
3. **Given** some runs exist but the specified ID does not match any, **When** the user runs `specmetrics export run <wrong-id>`, **Then** the error message includes the list of available IDs

---

### Edge Cases

- What happens when `.specmetrics/runs/` directory does not exist? The measure command should create it on first run.
- What happens when the `exports/` directory already contains files from a previous export? Existing files should be overwritten.
- What happens when `--export` is combined with an invalid `--format`? The error should be surfaced with valid format options before any export runs.
- What happens when the user runs `measure` twice without `--export`? Two separate run directories should exist under `.specmetrics/runs/`.
- What happens when a stage has no data (e.g., no errors)? The corresponding export file should still be created with empty content rather than omitted, to maintain a predictable file set.

## Constitution Check

**Engaged Principles**:

- **I (Specification First)** — The measure command still consumes software specifications as its primary input; the measure ID and export features are orthogonal to the specification source.
- **V (Evidence First)** — By persisting each run's results to a dedicated directory with a unique ID, the system preserves traceability to the exact specification state, configuration, and plugin versions used in that measurement. The `exports/` output further makes evidence accessible in structured formats.
- **VII (Canonical Representation)** — The persisted JSON in `.specmetrics/runs/<measure-id>/` uses the canonical output schema, and the export command reads from this persisted representation rather than re-running the pipeline or accessing framework-specific artifacts.
- **VIII (Plugin-Oriented)** — The CSV and XML export conversion uses tabular normalization of per-stage data with generic serializers, keeping the conversion logic independent of the CFM-based exporter plugins. The `export list` command follows the existing plugin-based exporter pattern.
- **X (AI-Friendly by Design)** — The structured JSON per run and the export output (JSON, CSV, XML) are all machine-consumable formats suitable for AI agents, CI pipelines, and analytics tools.
- **XI (Observability as a Native Capability)** — The run directory with IDs creates an audit trail of all measurements. The `export list` command makes this observability data discoverable. Each run's persisted data can feed into dashboards and engineering analytics.
- **XIV (Layer Independence)** — The export layer reads from persisted JSON files rather than depending on any pipeline stage or internal data structure. The CLI commands (`measure`, `export list`, `export run`) are interaction-layer concerns that do not affect the measurement or extraction layers.

**Compliance Notes**: Principle V is satisfied because each run directory is a self-contained evidence package with a unique ID linking back to the exact measurement context. Principle VII is satisfied because the export command reads from the canonical JSON output rather than re-running framework-specific adapters. Principle VIII is satisfied by keeping CSV/XML conversion as lightweight tabular normalization decoupled from CFM-specific plugins. Principle XIV is satisfied because the export layer has no dependency on pipeline internals — it reads persisted files only.

## Requirements

### Functional Requirements

- **FR-001**: The `measure` command MUST generate a unique measure ID for each execution and print it to stdout in the format `Measure ID: <id>`
- **FR-002**: The `measure` command MUST create a directory `.specmetrics/runs/<measure-id>/` and persist the measurement result as JSON file(s) inside it
- **FR-003**: The JSON persisted in `.specmetrics/runs/<measure-id>/` MUST use the same structure as the `export run` command's JSON output
- **FR-004**: The `specmetrics-output.json` file MUST include a `measure.id` field containing the measure ID, placed before the `measure.sdd_framework` field
- **FR-005**: The `specmetrics-output.json` file MUST include a `measure.id_path` field containing the measure-id folder name (e.g., `<measure-id>`)
- **FR-006**: The `measure` command MUST accept an `--export` flag; when present, the command MUST automatically invoke `export run` using the same measure ID after measurement completes
- **FR-007**: The `measure` command MUST accept a `--format` option (values: `json`, `csv`, `xml`, or comma-separated combinations); when combined with `--export`, this format MUST be passed to the automatic `export run`
- **FR-008**: When `--export` is provided without `--format`, the default format for the automatic export MUST be `json`
- **FR-009**: The `export list` command MUST list all available measure IDs from `.specmetrics/runs/`, ordered from most recent to oldest, showing at minimum the ID and creation timestamp
- **FR-010**: If no measure runs exist, `export list` MUST display a message indicating no runs are available
- **FR-011**: The `export run` command MUST accept an optional positional argument `<measure-id>`; if omitted, the command MUST use the most recent measure run (determined by the latest creation timestamp in `.specmetrics/runs/`)
- **FR-012**: The `export run` command MUST accept a `--format` option with default value `json`; supported values are `json`, `csv`, `xml`, or comma-separated combinations
- **FR-013**: When the specified `<measure-id>` does not exist, `export run` MUST display an error message: "Measure run `<id>` not found."
- **FR-014**: When no measure runs exist and no `<measure-id>` is provided, `export run` MUST fall back to running the measurement pipeline directly (backward compatible with the existing `export run` behavior)
- **FR-015**: The `export run` command MUST write output files to the `exports/` directory in the project root
- **FR-016**: For JSON format, `export run` MUST copy the files from `.specmetrics/runs/<measure-id>/` directly to `exports/` without modification
- **FR-017**: For CSV and XML formats, `export run` MUST normalize each stage's data to a tabular format (rows and columns appropriate to that stage's content type) and serialize it using generic CSV/XML writers
- **FR-018**: The `exports/` MUST contain one file per pipeline stage, where:
  - Stages that identified "documents" export document names and relative paths
  - Stages that identified "items" export the items and their contents
  - Stages that identified "metrics" export the metric names and their results
- **FR-019**: The README.md MUST be updated to document the new command syntaxes: `specmetrics measure [--export] [--format]`, `specmetrics export list`, and `specmetrics export run [<measure-id>] [--format]`

### Key Entities

- **Measure Run**: A single execution of the measurement pipeline, identified by a unique measure ID. Each run produces a self-contained result directory under `.specmetrics/runs/<measure-id>/` with JSON files capturing per-stage outcomes.
- **Measure ID**: A unique identifier in timestamp-prefixed UUID format (`YYYYMMDD-HHMMSS-<short-uuid>`) generated per measure execution. The timestamp portion encodes creation time for ordering; the short-uuid suffix ensures uniqueness. Used to locate the run's result directory and to reference the run in export commands.
- **Run Directory**: The `.specmetrics/runs/<measure-id>/` folder containing the persisted JSON output of that specific measurement run. This is the source for all export operations.
- **Export Stage File**: A file in the `exports/` directory representing one pipeline stage's data, converted to the requested format (JSON, CSV, or XML). The content structure varies by stage: documents list, items with content, or metrics with results.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Running `specmetrics measure` prints a unique ID and creates `.specmetrics/runs/<id>/` with the JSON result within the same time as a regular measure execution (no significant performance overhead from the file copy)
- **SC-002**: Running `specmetrics measure --export` completes both measurement and export in a single invocation, producing files in both `.specmetrics/runs/<id>/` and `exports/`
- **SC-003**: Running `specmetrics export list` after N measure runs displays exactly N entries, each with a valid measure ID and timestamp
- **SC-004**: Running `specmetrics export run` (without arguments) on a project with multiple measure runs exports the most recent one
- **SC-005**: Running `specmetrics export run <nonexistent-id>` produces an error within 1 second, clearly indicating the ID was not found
- **SC-006**: The `exports/` directory contains one file per stage for each requested format, and the files are valid in their respective format (JSON is valid JSON, CSV is valid CSV, XML is valid XML)
- **SC-007**: For JSON format exports, the files in `exports/` are byte-identical to the source files in `.specmetrics/runs/<measure-id>/`
- **SC-008**: Exporting the same measure run twice produces identical files in `exports/` (deterministic output)

## Assumptions

- The measure ID uses a timestamp-prefixed UUID format (`YYYYMMDD-HHMMSS-<short-uuid>`), where the timestamp portion encodes the creation time for ordering and the short-uuid ensures uniqueness
- The `.specmetrics/runs/` directory is created automatically on the first `measure` run if it does not exist
- The existing `specmetrics-output.json` continues to be written alongside the new per-run JSON files — the new `measure.id` and `measure.id_path` fields are added to it
- The per-stage files stored in `.specmetrics/runs/<measure-id>/` follow a naming convention like `<stage_name>.json` (e.g., `discover.json`, `extract.json`, `measure.json`)
- The `exports/` directory is created automatically by `export run` if it does not exist
- CSV and XML conversion uses tabular normalization (general-purpose rows+columns serialization) per stage; this is separate from the CFM-based exporter plugins which retain their original purpose
- The `export run` command's default `--format` changes from the current `"json,csv,xml"` to `"json"` to align with this feature's specification

## Clarifications

### Session 2026-07-20

- Q: What format should the measure ID use — pure UUID (requires separate metadata for ordering) or timestamp-embedded? → A: Timestamp-prefixed UUID (`YYYYMMDD-HHMMSS-<short-uuid>`), encoding creation time directly in the directory name for ordering while the short-uuid suffix guarantees uniqueness.
- Q: When no measure runs exist, should `export run` show an error or fall back to running the pipeline directly (old behavior)? → A: Fall back to running the pipeline directly (backward compatible). The new read-from-run-directory behavior applies when runs exist.
- Q: How should per-stage data (documents, items, metrics) be converted to CSV/XML, given existing exporter plugins expect CFM Measurement objects? → A: Normalize each stage's data to a tabular format (rows+columns) and use generic CSV/XML serializers, independent of the CFM-based exporter plugins.
