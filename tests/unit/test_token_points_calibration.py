from __future__ import annotations

import tempfile
from pathlib import Path

from specmetrics.plugins.calibration.loader import (
    discover_and_load_calibration,
    discover_calibration_files,
    load_calibration_file,
    merge_calibration_data,
)
from specmetrics.plugins.calibration.models import CalibrationProfile
from specmetrics.plugins.calibration.validator import validate_calibration_profile
from specmetrics.plugins.measurement.token_points.calibration import (
    get_default_calibration,
)


class TestDefaultCalibration:
    def test_load_default_calibration(self):
        profile = get_default_calibration()
        assert profile.version == "1.0"
        assert profile.specification_cost.decisions == 1.5
        assert profile.specification_cost.assumptions == 1.0
        assert profile.specification_cost.constraints == 1.5
        assert profile.specification_cost.risks == 2.0
        assert profile.specification_cost.open_questions == 1.0
        assert profile.specification_cost.acceptance_criteria == 1.0
        assert profile.specification_cost.glossary_terms == 0.5
        assert profile.specification_cost.references == 1.0
        assert profile.content_multiplier == 0.1

        assert profile.code_generation_cost.functional_processes == 5.0
        assert profile.code_generation_cost.business_rules == 3.0
        assert profile.code_generation_cost.operations == 2.0
        assert profile.code_generation_cost.data_groups == 2.0
        assert profile.code_generation_cost.relationships == 1.0
        assert profile.code_generation_cost.actors == 1.0

    def test_default_activities(self):
        profile = get_default_calibration()
        assert profile.specification_cost.activities == {
            "exploration": 2.0,
            "clarification": 3.0,
            "refinement": 3.0,
            "review": 1.5,
            "validation": 2.0,
        }


class TestCalibrationLoading:
    def test_yaml_override_specific_keys(self):
        default = get_default_calibration()
        override_data = {
            "version": "1.0",
            "specification_cost": {
                "decisions": 3.0,
                "assumptions": 2.0,
            },
            "code_generation_cost": {
                "functional_processes": 8.0,
            },
        }
        merged = merge_calibration_data(default, override_data)
        assert merged.specification_cost.decisions == 3.0
        assert merged.specification_cost.assumptions == 2.0
        assert merged.specification_cost.constraints == 1.5
        assert merged.code_generation_cost.functional_processes == 8.0
        assert merged.code_generation_cost.business_rules == 3.0

    def test_discover_no_directory(self):
        files = discover_calibration_files("/nonexistent/path")
        assert files == []

    def test_discover_with_yaml_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "test.yml").write_text("version: '1.0'\n")
            files = discover_calibration_files(tmp)
            assert len(files) == 1
            assert files[0].name == "test.yml"

    def test_load_file(self):
        import yaml

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "profile.yml")
            path.write_text(
                yaml.dump({"version": "1.0", "specification_cost": {"decisions": 2.0}})
            )
            data = load_calibration_file(str(path))
            assert data is not None
            assert data["version"] == "1.0"
            assert data["specification_cost"]["decisions"] == 2.0

    def test_load_invalid_file(self):
        data = load_calibration_file("/nonexistent/file.yml")
        assert data is None

    def test_discover_and_load_multiple_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "base.yml").write_text(
                "version: '1.0'\nspecification_cost:\n  decisions: 2.0\n"
            )
            Path(tmp, "override.yml").write_text(
                "specification_cost:\n  assumptions: 3.0\n"
            )
            profile = discover_and_load_calibration(tmp, CalibrationProfile())
            assert profile is not None
            assert profile.specification_cost.decisions == 2.0
            assert profile.specification_cost.assumptions == 3.0


class TestCalibrationValidator:
    def test_valid_profile(self):
        data = {
            "version": "1.0.0",
            "specification_cost": {
                "decisions": 1.5,
                "assumptions": 1.0,
            },
            "code_generation_cost": {
                "functional_processes": 5.0,
            },
        }
        errors = validate_calibration_profile(data)
        assert errors == []

    def test_invalid_semver(self):
        data = {
            "version": "not-semver",
            "specification_cost": {},
            "code_generation_cost": {},
        }
        errors = validate_calibration_profile(data)
        assert any("version" in e and "semver" in e for e in errors)

    def test_negative_weight(self):
        data = {
            "version": "1.0.0",
            "specification_cost": {"decisions": -1.0},
            "code_generation_cost": {"functional_processes": 5.0},
        }
        errors = validate_calibration_profile(data)
        assert any("non-negative" in e for e in errors)

    def test_non_numeric_weight(self):
        data = {
            "version": "1.0.0",
            "specification_cost": {"decisions": "high"},
            "code_generation_cost": {"functional_processes": 5.0},
        }
        errors = validate_calibration_profile(data)
        assert any("non-negative" in e for e in errors)
