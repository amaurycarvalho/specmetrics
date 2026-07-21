from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from specmetrics.plugins.measurement.storypoints.calibrator import (
    DEFAULT_CFM_BASE_WEIGHTS,
    DEFAULT_CSM_BASE_WEIGHTS,
    DEFAULT_FACTOR_COEFFICIENTS,
    DEFAULT_FIBONACCI_SCALE,
    StoryPointsCalibrationProfile,
    get_default_calibration,
    load_calibration,
)


class TestStoryPointsCalibrationProfile:
    def test_defaults(self):
        profile = StoryPointsCalibrationProfile()
        assert profile.version == "1.0"
        assert profile.content_multiplier == 0.1
        assert profile.factor_coefficients == DEFAULT_FACTOR_COEFFICIENTS
        assert profile.csm_base_weights == DEFAULT_CSM_BASE_WEIGHTS
        assert profile.cfm_base_weights == DEFAULT_CFM_BASE_WEIGHTS
        assert profile.default_fallback_weight == 1.0
        assert profile.fibonacci_scale == DEFAULT_FIBONACCI_SCALE
        assert profile.ranking_strategy == "percentile"

    def test_negative_content_multiplier(self):
        with pytest.raises(ValueError, match="content_multiplier"):
            StoryPointsCalibrationProfile(content_multiplier=-0.1)

    def test_negative_factor_coefficient(self):
        with pytest.raises(ValueError, match="factor_coefficients"):
            StoryPointsCalibrationProfile(
                factor_coefficients={"business_interactions": -1.0}
            )

    def test_negative_csm_weight(self):
        with pytest.raises(ValueError, match="csm_base_weights"):
            StoryPointsCalibrationProfile(
                csm_base_weights={"decision": -1.0}
            )

    def test_negative_cfm_weight(self):
        with pytest.raises(ValueError, match="cfm_base_weights"):
            StoryPointsCalibrationProfile(
                cfm_base_weights={"actor": -1.0}
            )

    def test_negative_fallback_weight(self):
        with pytest.raises(ValueError, match="default_fallback_weight"):
            StoryPointsCalibrationProfile(default_fallback_weight=-0.5)

    def test_fibonacci_scale_too_short(self):
        with pytest.raises(ValueError, match="fibonacci_scale"):
            StoryPointsCalibrationProfile(fibonacci_scale=[1])

    def test_fibonacci_scale_unsorted(self):
        with pytest.raises(ValueError, match="fibonacci_scale"):
            StoryPointsCalibrationProfile(fibonacci_scale=[5, 1, 3])

    def test_invalid_ranking_strategy(self):
        with pytest.raises(ValueError, match="ranking_strategy"):
            StoryPointsCalibrationProfile(ranking_strategy="linear")

    def test_custom_values(self):
        profile = StoryPointsCalibrationProfile(
            content_multiplier=0.5,
            factor_coefficients={"business_interactions": 2.0},
            csm_base_weights={"decision": 8.0},
            cfm_base_weights={"actor": 0.5},
            default_fallback_weight=0.5,
            fibonacci_scale=[1, 2, 3, 5, 8],
            ranking_strategy="percentile",
        )
        assert profile.content_multiplier == 0.5
        assert profile.factor_coefficients["business_interactions"] == 2.0
        assert profile.csm_base_weights["decision"] == 8.0
        assert profile.cfm_base_weights["actor"] == 0.5
        assert profile.default_fallback_weight == 0.5
        assert profile.fibonacci_scale == [1, 2, 3, 5, 8]


class TestGetDefaultCalibration:
    def test_returns_default_profile(self):
        profile = get_default_calibration()
        assert isinstance(profile, StoryPointsCalibrationProfile)
        assert profile.content_multiplier == 0.1

    def test_defaults_match_profile_defaults(self):
        default = get_default_calibration()
        direct = StoryPointsCalibrationProfile()
        assert default.model_dump() == direct.model_dump()


class TestLoadCalibration:
    def test_none_dir_returns_default(self):
        profile = load_calibration(None)
        assert profile.content_multiplier == 0.1

    def test_nonexistent_dir_returns_default(self):
        profile = load_calibration("/nonexistent/path")
        assert profile.content_multiplier == 0.1

    def test_empty_dir_returns_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            profile = load_calibration(tmpdir)
        assert profile.content_multiplier == 0.1

    def test_loads_yaml_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cal_data = {"content_multiplier": 0.5}
            cal_path = Path(tmpdir) / "calibration.yaml"
            with open(cal_path, "w") as f:
                yaml.dump(cal_data, f)
            profile = load_calibration(tmpdir)
        assert profile.content_multiplier == 0.5

    def test_loads_yml_extension(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cal_data = {"content_multiplier": 0.3}
            cal_path = Path(tmpdir) / "calibration.yml"
            with open(cal_path, "w") as f:
                yaml.dump(cal_data, f)
            profile = load_calibration(tmpdir)
        assert profile.content_multiplier == 0.3

    def test_merge_multiple_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(Path(tmpdir) / "a.yaml", "w") as f:
                yaml.dump({"content_multiplier": 0.5}, f)
            with open(Path(tmpdir) / "b.yaml", "w") as f:
                yaml.dump({"default_fallback_weight": 2.0}, f)
            profile = load_calibration(tmpdir)
        assert profile.content_multiplier == 0.5
        assert profile.default_fallback_weight == 2.0

    def test_minimal_yaml_loads_defaults(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(Path(tmpdir) / "cal.yaml", "w") as f:
                yaml.dump({"version": "1.0"}, f)
            profile = load_calibration(tmpdir)
        assert profile.content_multiplier == 0.1
        assert profile.factor_coefficients == DEFAULT_FACTOR_COEFFICIENTS
        assert profile.csm_base_weights == DEFAULT_CSM_BASE_WEIGHTS

    def test_backward_compatible_missing_fields(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(Path(tmpdir) / "old.yaml", "w") as f:
                yaml.dump({"version": "0.9"}, f)
            profile = load_calibration(tmpdir)
        assert profile.content_multiplier == 0.1


class TestUserStory4CalibrationIntegration:
    def test_custom_content_multiplier_affects_scores(self):
        from specmetrics.plugins.measurement.storypoints.calculator import calculate
        from tests.unit.test_storypoints_calculator import _make_cfm_with_descriptions
        cfm = _make_cfm_with_descriptions([
            ("fp-001", "Test", "some description for testing purposes"),
        ])
        cal_default = StoryPointsCalibrationProfile(content_multiplier=0.1)
        cal_custom = StoryPointsCalibrationProfile(content_multiplier=0.5)
        result_default = calculate(cfm, run_id="us4-def", calibration=cal_default)
        result_custom = calculate(cfm, run_id="us4-cus", calibration=cal_custom)
        assert result_custom.content_multiplier == 0.5
        fp_def = [i for i in result_default.items if i.element_type == "functional_process"][0]
        fp_cus = [i for i in result_custom.items if i.element_type == "functional_process"][0]
        expected_ratio = 0.5 / 0.1
        actual_ratio = (fp_cus.content_score / fp_def.content_score) if fp_def.content_score > 0 else 0.0
        assert abs(actual_ratio - expected_ratio) < 0.01

    def test_custom_csm_base_weight_override(self):
        cal = StoryPointsCalibrationProfile(
            csm_base_weights={"decision": 8.0},
        )
        assert cal.csm_base_weights["decision"] == 8.0

    def test_minimal_calibration_loads_defaults(self):
        cal = StoryPointsCalibrationProfile(version="1.0")
        assert cal.content_multiplier == 0.1
        assert len(cal.factor_coefficients) == 6
        assert len(cal.csm_base_weights) == 13
        assert len(cal.cfm_base_weights) == 5

    def test_custom_factor_coefficients_override(self):
        from specmetrics.plugins.measurement.storypoints.calculator import calculate
        from tests.unit.test_storypoints_calculator import _make_cfm_with_descriptions
        cfm = _make_cfm_with_descriptions([
            ("fp-001", "Test", "desc"),
        ])
        cal_default = StoryPointsCalibrationProfile()
        cal_custom = StoryPointsCalibrationProfile(
            factor_coefficients={"business_interactions": 10.0},
        )
        result_default = calculate(cfm, run_id="us4-fdef", calibration=cal_default)
        result_custom = calculate(cfm, run_id="us4-fcus", calibration=cal_custom)
        assert result_custom.total_raw_score != result_default.total_raw_score
