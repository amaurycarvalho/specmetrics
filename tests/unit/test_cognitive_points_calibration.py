from __future__ import annotations

import tempfile
from pathlib import Path

from specmetrics.plugins.measurement.cognitive_points.calibration import (
    CognitiveCalibrationProfile,
    FibonacciNormalizationProfile,
    get_default_calibration,
    load_calibration,
)


class TestDefaultCalibration:
    def test_load_default_calibration(self):
        profile = get_default_calibration()
        assert profile.version == "1.0"
        assert profile.bloom_levels["remember"] == 1.0
        assert profile.bloom_levels["understand"] == 2.0
        assert profile.bloom_levels["apply"] == 3.0
        assert profile.bloom_levels["analyze"] == 4.0
        assert profile.bloom_levels["evaluate"] == 5.0
        assert profile.bloom_levels["create"] == 8.0
        assert profile.default_bloom_level == "analyze"

    def test_default_bloom_mappings(self):
        profile = get_default_calibration()
        assert profile.bloom_mappings["decision"] == "evaluate"
        assert profile.bloom_mappings["functional_process"] == "create"
        assert profile.bloom_mappings["glossary_term"] == "remember"

    def test_default_fibonacci_profile(self):
        profile = get_default_calibration()
        assert profile.fibonacci_normalization.thresholds == [
            5, 12, 22, 35, 55, 85, 130
        ]
        assert profile.fibonacci_normalization.output_values == [
            1, 3, 5, 8, 13, 20, 40, 100
        ]


class TestCognitiveCalibrationProfile:
    def test_construct_with_overrides(self):
        profile = CognitiveCalibrationProfile(
            version="2.0",
            bloom_levels={"analyze": 5.0},
            bloom_mappings={"decision": "analyze"},
            default_bloom_level="apply",
            fibonacci_normalization=FibonacciNormalizationProfile(
                thresholds=[1, 2, 3], output_values=[1, 2, 3, 4]
            ),
        )
        assert profile.version == "2.0"
        assert profile.bloom_levels["analyze"] == 5.0
        assert profile.bloom_mappings["decision"] == "analyze"
        assert profile.default_bloom_level == "apply"
        assert profile.fibonacci_normalization.output_values == [1, 2, 3, 4]


class TestCalibrationLoading:
    def test_load_without_directory_returns_default(self):
        profile = load_calibration()
        assert profile.version == "1.0"
        assert profile.bloom_levels["create"] == 8.0

    def test_load_nonexistent_directory_returns_default(self):
        profile = load_calibration("/nonexistent/path")
        assert profile.version == "1.0"

    def test_yaml_override_bloom_levels(self):
        with tempfile.TemporaryDirectory() as tmp:
            yaml_path = Path(tmp, "cognitive-points.yml")
            yaml_path.write_text(
                "version: '1.0'\n"
                "bloom_levels:\n"
                "  create: 10.0\n"
                "  analyze: 5.0\n"
            )
            profile = load_calibration(tmp)
            assert profile.bloom_levels["create"] == 10.0
            assert profile.bloom_levels["analyze"] == 5.0
            assert profile.bloom_levels["remember"] == 1.0

    def test_yaml_override_bloom_mappings(self):
        with tempfile.TemporaryDirectory() as tmp:
            yaml_path = Path(tmp, "cognitive-points.yml")
            yaml_path.write_text(
                "version: '1.0'\n"
                "bloom_mappings:\n"
                "  decision: remember\n"
            )
            profile = load_calibration(tmp)
            assert profile.bloom_mappings["decision"] == "remember"
            assert profile.bloom_mappings["functional_process"] == "create"

    def test_yaml_override_fibonacci(self):
        with tempfile.TemporaryDirectory() as tmp:
            yaml_path = Path(tmp, "cognitive-points.yml")
            yaml_path.write_text(
                "version: '1.0'\n"
                "fibonacci_normalization:\n"
                "  thresholds: [10, 20]\n"
                "  output_values: [1, 5, 10]\n"
            )
            profile = load_calibration(tmp)
            assert profile.fibonacci_normalization.thresholds == [10, 20]
            assert profile.fibonacci_normalization.output_values == [1, 5, 10]

    def test_yaml_override_default_bloom_level(self):
        with tempfile.TemporaryDirectory() as tmp:
            yaml_path = Path(tmp, "cognitive-points.yml")
            yaml_path.write_text(
                "version: '1.0'\n"
                "default_bloom_level: remember\n"
            )
            profile = load_calibration(tmp)
            assert profile.default_bloom_level == "remember"

    def test_yaml_invalid_file_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            yaml_path = Path(tmp, "cognitive-points.yml")
            yaml_path.write_text("invalid: yaml: : :\n")
            profile = load_calibration(tmp)
            assert profile.version == "1.0"

    def test_yaml_empty_file_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            yaml_path = Path(tmp, "cognitive-points.yml")
            yaml_path.write_text("")
            profile = load_calibration(tmp)
            assert profile.version == "1.0"

    def test_multiple_yaml_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "base.yml").write_text(
                "version: '1.0'\n"
                "bloom_levels:\n"
                "  analyze: 5.0\n"
            )
            Path(tmp, "override.yml").write_text(
                "bloom_levels:\n"
                "  create: 12.0\n"
            )
            profile = load_calibration(tmp)
            assert profile.bloom_levels["analyze"] == 5.0
            assert profile.bloom_levels["create"] == 12.0
            assert profile.bloom_levels["remember"] == 1.0


class TestFibonacciNormalizationProfile:
    def test_default_constructor(self):
        profile = FibonacciNormalizationProfile()
        assert len(profile.output_values) == len(profile.thresholds) + 1

    def test_validation_error(self):
        import pytest

        with pytest.raises(ValueError, match="len.*must equal"):
            FibonacciNormalizationProfile(
                thresholds=[1, 2], output_values=[1, 2, 3, 4]
            )
