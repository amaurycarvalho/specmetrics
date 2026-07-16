from __future__ import annotations

from pathlib import Path

from specmetrics.kernel.validation.pipeline import ValidationPipeline


def _write_spec(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


class TestValidationPipeline:
    def test_run_structural_only(self, tmp_path):
        spec = _write_spec(
            tmp_path / "spec.md",
            "## User Scenarios & Testing\ncontent\n"
            "## Constitution Check\ncontent\n"
            "## Requirements\ncontent\n"
            "## Success Criteria\ncontent\n"
            "## Assumptions\ncontent\n",
        )
        pipeline = ValidationPipeline()
        report = pipeline.run(spec, mode="structural")
        assert report.overall_passed

    def test_run_full_valid(self, tmp_path):
        spec = _write_spec(
            tmp_path / "spec.md",
            "## User Scenarios & Testing\ncontent\n"
            "## Constitution Check\n\n"
            "**Engaged Principles**: I (Specification First)\n\n"
            "**Compliance Notes**: All good.\n"
            "## Requirements\ncontent\n"
            "## Success Criteria\ncontent\n"
            "## Assumptions\ncontent\n",
        )
        pipeline = ValidationPipeline()
        report = pipeline.run(spec)
        assert report.overall_passed

    def test_run_invalid(self, tmp_path):
        spec = _write_spec(tmp_path / "spec.md", "")
        pipeline = ValidationPipeline()
        report = pipeline.run(spec)
        assert not report.overall_passed

    def test_batch_validation(self, tmp_path):
        valid = _write_spec(
            tmp_path / "valid.md",
            "## User Scenarios & Testing\n"
            "## Constitution Check\n\n"
            "**Engaged Principles**: I (Specification First)\n\n"
            "**Compliance Notes**: All good.\n"
            "## Requirements\n"
            "## Success Criteria\n"
            "## Assumptions\n",
        )
        invalid = _write_spec(tmp_path / "invalid.md", "")
        pipeline = ValidationPipeline()
        batch = pipeline.run_batch([valid, invalid])
        assert batch.total_documents == 2
