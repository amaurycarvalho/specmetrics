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
        assert profile.default_bloom_level == "understand"

    def test_default_bloom_mappings(self):
        profile = get_default_calibration()
        assert profile.bloom_mappings["decision"] == "evaluate"
        assert profile.bloom_mappings["functional_process"] == "create"
        assert profile.bloom_mappings["glossary_term"] == "remember"

    def test_default_fibonacci_profile(self):
        profile = get_default_calibration()
        assert profile.fibonacci_normalization.thresholds == [
            5,
            12,
            22,
            35,
            55,
            85,
            130,
        ]
        assert profile.fibonacci_normalization.output_values == [
            1,
            3,
            5,
            8,
            13,
            20,
            40,
            100,
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
                "version: '1.0'\nbloom_levels:\n  create: 10.0\n  analyze: 5.0\n"
            )
            profile = load_calibration(tmp)
            assert profile.bloom_levels["create"] == 10.0
            assert profile.bloom_levels["analyze"] == 5.0
            assert profile.bloom_levels["remember"] == 1.0

    def test_yaml_override_bloom_mappings(self):
        with tempfile.TemporaryDirectory() as tmp:
            yaml_path = Path(tmp, "cognitive-points.yml")
            yaml_path.write_text(
                "version: '1.0'\nbloom_mappings:\n  decision: remember\n"
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
            yaml_path.write_text("version: '1.0'\ndefault_bloom_level: remember\n")
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

    def test_yaml_override_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            yaml_path = Path(tmp, "cognitive-points.yml")
            yaml_path.write_text("version: '2.0'\n")
            profile = load_calibration(tmp)
            assert profile.version == "2.0"

    def test_yaml_override_content_multiplier(self):
        with tempfile.TemporaryDirectory() as tmp:
            yaml_path = Path(tmp, "cognitive-points.yml")
            yaml_path.write_text("version: '1.0'\ncontent_multiplier: 0.5\n")
            profile = load_calibration(tmp)
            assert profile.content_multiplier == 0.5

    def test_yaml_fib_partial_output_values_keeps_base_thresholds(self):
        with tempfile.TemporaryDirectory() as tmp:
            yaml_path = Path(tmp, "cognitive-points.yml")
            yaml_path.write_text(
                "version: '1.0'\n"
                "fibonacci_normalization:\n"
                "  output_values: [1, 2, 3, 4, 5, 6, 7, 8]\n"
            )
            profile = load_calibration(tmp)
            assert profile.fibonacci_normalization.output_values == [1, 2, 3, 4, 5, 6, 7, 8]
            assert profile.fibonacci_normalization.thresholds == [
                5,
                12,
                22,
                35,
                55,
                85,
                130,
            ]

    def test_yaml_fib_partial_thresholds_keeps_base_output_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            yaml_path = Path(tmp, "cognitive-points.yml")
            yaml_path.write_text(
                "version: '1.0'\n"
                "fibonacci_normalization:\n"
                "  thresholds: [1, 2]\n"
                "  output_values: [1, 2, 3]\n"
            )
            profile = load_calibration(tmp)
            assert profile.fibonacci_normalization.thresholds == [1, 2]
            assert profile.fibonacci_normalization.output_values == [1, 2, 3]

    def test_yaml_extension_loaded(self):
        with tempfile.TemporaryDirectory() as tmp:
            yaml_path = Path(tmp, "cognitive-points.yaml")
            yaml_path.write_text("version: '1.0'\nbloom_levels:\n  create: 9.0\n")
            profile = load_calibration(tmp)
            assert profile.bloom_levels["create"] == 9.0

    def test_multiple_yaml_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "base.yml").write_text(
                "version: '1.0'\nbloom_levels:\n  analyze: 5.0\n"
            )
            Path(tmp, "override.yml").write_text("bloom_levels:\n  create: 12.0\n")
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
            FibonacciNormalizationProfile(thresholds=[1, 2], output_values=[1, 2, 3, 4])


class TestMergeCalibrationData:
    def _merge(self, overrides):
        from specmetrics.plugins.measurement.cognitive_points.calibration import (
            _merge_calibration_data,
        )

        return _merge_calibration_data(get_default_calibration(), overrides)

    def test_version_override_applied(self):
        """Kills _merge_calibration_data__mutmut_2/6/7 (version key lookup)."""
        merged = self._merge({"version": "2.0"})
        assert merged.version == "2.0"

    def test_content_multiplier_override_applied(self):
        """Kills _merge_calibration_data__mutmut_34/38/39 (content_multiplier key lookup)."""
        merged = self._merge({"content_multiplier": 0.5})
        assert merged.content_multiplier == 0.5

    def test_fib_partial_thresholds_keeps_base_output_values(self):
        """Kills _merge_calibration_data__mutmut_49/51 (thresholds default resolution)."""
        merged = self._merge(
            {"fibonacci_normalization": {"output_values": [1, 2, 3, 4, 5, 6, 7, 8]}}
        )
        assert merged.fibonacci_normalization.output_values == [1, 2, 3, 4, 5, 6, 7, 8]
        assert merged.fibonacci_normalization.thresholds == [
            5,
            12,
            22,
            35,
            55,
            85,
            130,
        ]

    def test_fib_empty_override_keeps_base_profile(self):
        """Kills _merge_calibration_data__mutmut_49/51/56/58 (both defaults)."""
        merged = self._merge({"fibonacci_normalization": {}})
        assert merged.fibonacci_normalization.thresholds == [
            5,
            12,
            22,
            35,
            55,
            85,
            130,
        ]
        assert merged.fibonacci_normalization.output_values == [
            1,
            3,
            5,
            8,
            13,
            20,
            40,
            100,
        ]

    def test_fib_partial_thresholds_only_raises_validation_error(self):
        """Kills _merge_calibration_data__mutmut_56/58 (output_values must stay valid)."""
        import pytest

        with pytest.raises(ValueError, match="len.*must equal"):
            self._merge(
                {"fibonacci_normalization": {"thresholds": [1, 2, 3]}}
            )

    def test_version_constructor_argument_preserved(self):
        """Kills _merge_calibration_data__mutmut_72 (version= arg deleted)."""
        merged = self._merge({"version": "3.1"})
        assert merged.version == "3.1"

    def test_content_multiplier_constructor_argument_preserved(self):
        """Kills _merge_calibration_data__mutmut_76 (content_multiplier= arg deleted)."""
        merged = self._merge({"content_multiplier": 0.75})
        assert merged.content_multiplier == 0.75


class TestLoadCalibrationFile:
    def test_loads_yml_file_into_plain_dict(self):
        """Kills _load_calibration_file__mutmut_2 (YAML safe typ replaced with None)."""
        from specmetrics.plugins.measurement.cognitive_points.calibration import (
            _load_calibration_file,
        )

        with tempfile.TemporaryDirectory() as tmp:
            yaml_path = Path(tmp, "profile.yml")
            yaml_path.write_text(
                "version: '1.0'\nbloom_levels:\n  create: 10.0\n"
            )
            data = _load_calibration_file(yaml_path)
            assert isinstance(data, dict)
            assert data["version"] == "1.0"
            assert data["bloom_levels"]["create"] == 10.0

    def test_non_dict_yaml_returns_none(self):
        """Kills _load_calibration_file__mutmut_2 (safe typ parsing of scalars)."""
        from specmetrics.plugins.measurement.cognitive_points.calibration import (
            _load_calibration_file,
        )

        with tempfile.TemporaryDirectory() as tmp:
            yaml_path = Path(tmp, "scalar.yml")
            yaml_path.write_text("just a scalar\n")
            assert _load_calibration_file(yaml_path) is None
