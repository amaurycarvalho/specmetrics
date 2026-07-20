# Research: Clean Command for Runs Housekeeping

## No Unresolved Clarifications

The feature spec [spec.md](spec.md) contains no [NEEDS CLARIFICATION] markers. All details are explicitly specified:

| Parameter | Default | Behavior |
|-----------|---------|----------|
| `--keep-runs` | 90 | 0 disables run-count retention |
| `--keep-days` | 30 | 0 disables age-based retention |
| `--dry-run` | false | Preview mode — no actual deletion |

## Technology Decisions

### CLI Framework: Typer (existing)

The existing `specmetrics` CLI uses Typer. The `clean` command will be registered as an `@app.command()` on the main `typer.Typer` app, consistent with `measure` and `version` commands.

- **Rationale**: Zero new dependencies. Typer is already `pyproject.toml` dependency.
- **Alternatives considered**: None — must match existing CLI conventions.

### Run Folder Discovery: `pathlib.Path.iterdir()` + regex

Run folders follow the naming convention `YYYYMMDD-HHMMSS-<uuid>`. A regex `^\d{8}-\d{6}-[a-f0-9-]+$` identifies valid run folders.

- **Rationale**: Simple, cross-platform, no external dependencies.
- **Alternatives considered**: `glob` patterns — less precise for filtering invalid entries.

### Deletion: `shutil.rmtree()`

Python's `shutil.rmtree` handles recursive directory deletion cross-platform.

- **Rationale**: Standard library, handles nested files, cross-platform.
- **Edge case**: Permission errors are caught per-folder and logged as warnings, continuing with remaining folders.

### Performance: Batch timestamp parsing

Folder names are parsed using `datetime.strptime(name[:15], "%Y%m%d-%H%M%S")`. For 1000 folders, this completes in well under 100ms.

- **Rationale**: Simple string slicing + stdlib datetime is sufficient for the target of 1000 folders in <1s.
- **Alternatives considered**: `pathlib.stat().st_ctime` — less reliable for determining the "most recent" run, as spec requires folder name ordering.

### Testing: `pytest` + `typer.testing.CliRunner` + `tmp_path`

Existing project uses pytest. CLI tests use `CliRunner` from `typer.testing`. Filesystem isolation via `pytest`'s `tmp_path` fixture.

- **Rationale**: Follows existing testing patterns in `tests/cli/test_app.py` and `tests/cli/test_measure.py`.

## Cross-Platform Considerations

Windows compatibility requires:
- `shutil.rmtree` with `onerror` handler for permission/locked files (handles Windows file locking)
- `pathlib` for path operations (already used throughout the project)
- Avoid `os.chmod` patterns that differ on Windows
