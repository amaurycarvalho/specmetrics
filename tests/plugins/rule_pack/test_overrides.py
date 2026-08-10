from __future__ import annotations

from datetime import UTC, datetime

from specmetrics.kernel.cfm.metadata import BuildMetadata
from specmetrics.kernel.cfm.model import (
    CanonicalFunctionalModel,
    EvidenceRef,
    FunctionalProcess,
)
from specmetrics.plugins.rule_pack._overrides import (
    apply_complexity_overrides,
    apply_weight_overrides,
    mark_exclusions,
    rating_for,
    set_vaf,
)


def _make_cfm(
    processes: dict[str, dict] | None = None,
) -> CanonicalFunctionalModel:
    if processes is None:
        processes = {"fp-001": {"name": "Input", "function_type": "EI"}}
    metadata = BuildMetadata(
        run_id="test-run",
        created_at=datetime.now(UTC),
    )
    return CanonicalFunctionalModel(
        run_id="test-run",
        functional_processes={
            pid: FunctionalProcess(
                id=pid,
                name=props["name"],
                evidence=EvidenceRef(
                    graph_node_id=f"n-{pid}",
                    document_id="doc-1",
                    text=f"Process {props['name']}",
                ),
                metadata={
                    "function_type": props.get("function_type", "EI"),
                    **{
                        k: v
                        for k, v in props.items()
                        if k not in {"name", "function_type"}
                    },
                },
            )
            for pid, props in processes.items()
        },
        metadata=metadata,
    )


class TestRatingFor:
    def test_low_when_both_below_or_at_low_bound(self) -> None:
        assert rating_for({"det_count": 1, "ftr_count": 1}, {"det": [2, 8], "ftr": [1, 5]}) == "Low"

    def test_average_when_within_mid_bounds(self) -> None:
        assert rating_for({"det_count": 4, "ftr_count": 3}, {"det": [2, 8], "ftr": [1, 5]}) == "Average"

    def test_high_when_above_mid_bounds(self) -> None:
        assert rating_for({"det_count": 9, "ftr_count": 1}, {"det": [2, 8], "ftr": [1, 5]}) == "High"

    def test_high_by_ftr(self) -> None:
        assert rating_for({"det_count": 1, "ftr_count": 9}, {"det": [2, 8], "ftr": [1, 5]}) == "High"

    def test_boundaries_are_inclusive(self) -> None:
        assert rating_for({"det_count": 2, "ftr_count": 1}, {"det": [2, 8], "ftr": [1, 5]}) == "Low"
        assert rating_for({"det_count": 8, "ftr_count": 5}, {"det": [2, 8], "ftr": [1, 5]}) == "Average"

    def test_non_numeric_det_falls_back_to_rating(self) -> None:
        assert rating_for({"det_count": "x", "ftr_count": 1}, {"det": [2, 8]}) == "Average"
        assert rating_for(
            {"det_count": "x", "ftr_count": 1, "complexity_rating": "High"}, {"det": [2, 8]}
        ) == "High"

    def test_missing_counts_fall_back(self) -> None:
        assert rating_for({"function_type": "EI"}, {"det": [2, 8], "ftr": [1, 5]}) == "Low"
        assert rating_for(
            {"function_type": "EI", "det_count": "x"}, {"det": [2, 8], "ftr": [1, 5]}
        ) == "Average"
        assert rating_for(
            {"function_type": "EI", "det_count": "x", "complexity_rating": "High"},
            {"det": [2, 8], "ftr": [1, 5]},
        ) == "High"

    def test_default_thresholds_used_when_absent(self) -> None:
        assert rating_for({"det_count": 0, "ftr_count": 0}, {}) == "Low"
        assert rating_for({"det_count": 500, "ftr_count": 500}, {}) == "Average"
        assert rating_for({"det_count": 1000, "ftr_count": 1000}, {}) == "High"

    def test_missing_ftr_threshold_defaults(self) -> None:
        assert rating_for({"det_count": 1, "ftr_count": 1}, {"det": [2, 8]}) == "Average"
        assert rating_for({"det_count": 10, "ftr_count": 1}, {"det": [2, 8]}) == "High"

    def test_missing_det_count_default_zero(self) -> None:
        assert rating_for({"ftr_count": 0}, {"det": [0, 999], "ftr": [0, 999]}) == "Low"

    def test_missing_ftr_count_default_zero(self) -> None:
        assert rating_for({"det_count": 0}, {"det": [0, 999], "ftr": [0, 999]}) == "Low"

    def test_missing_det_defaults_low_bound_zero(self) -> None:
        assert rating_for(
            {"det_count": 1, "ftr_count": 0}, {"ftr": [0, 999]}
        ) == "Average"

    def test_missing_det_defaults_high_bound_999(self) -> None:
        assert rating_for(
            {"det_count": 1000, "ftr_count": 0}, {"ftr": [0, 999]}
        ) == "High"

    def test_missing_ftr_defaults_high_bound_999(self) -> None:
        assert rating_for(
            {"det_count": 0, "ftr_count": 1000}, {"det": [0, 999]}
        ) == "High"

    def test_det_between_bounds_uses_ftr_low_bound(self) -> None:
        assert rating_for(
            {"det_count": 5, "ftr_count": 0}, {"det": [2, 8], "ftr": [1, 5]}
        ) == "Average"


class TestMarkExclusions:
    def test_marks_by_element_id(self) -> None:
        cfm = _make_cfm(
            {
                "fp-001": {"name": "A", "function_type": "EI"},
                "fp-002": {"name": "B", "function_type": "EO"},
            }
        )
        result = mark_exclusions(cfm, set(), {"fp-002"})
        assert result.functional_processes["fp-002"].metadata["excluded"] is True
        assert result.functional_processes["fp-002"].metadata["excluded_by"] == "element_exclusion"
        assert result.functional_processes["fp-001"].metadata.get("excluded") is not True
        assert result is not cfm

    def test_marks_by_type(self) -> None:
        cfm = _make_cfm(
            {
                "fp-001": {"name": "A", "function_type": "EI"},
                "fp-002": {"name": "B", "function_type": "EQ"},
            }
        )
        result = mark_exclusions(cfm, {"EQ"}, set())
        assert result.functional_processes["fp-002"].metadata["excluded"] is True
        assert result.functional_processes["fp-002"].metadata["excluded_by"] == "type_exclusion:EQ"
        assert result.functional_processes["fp-001"].metadata.get("excluded") is not True

    def test_type_match_is_case_insensitive(self) -> None:
        cfm = _make_cfm(
            {
                "fp-001": {"name": "A", "function_type": "eq"},
            }
        )
        result = mark_exclusions(cfm, {"EQ"}, set())
        assert result.functional_processes["fp-001"].metadata["excluded"] is True

    def test_element_id_takes_precedence(self) -> None:
        cfm = _make_cfm(
            {
                "fp-001": {"name": "A", "function_type": "eq"},
            }
        )
        result = mark_exclusions(cfm, {"EQ"}, {"fp-001"})
        assert result.functional_processes["fp-001"].metadata["excluded_by"] == "element_exclusion"

    def test_original_left_untouched(self) -> None:
        cfm = _make_cfm({"fp-001": {"name": "A", "function_type": "EQ"}})
        mark_exclusions(cfm, {"EQ"}, set())
        assert cfm.functional_processes["fp-001"].metadata.get("excluded") is not True

    def _cfm_without_function_type(self) -> CanonicalFunctionalModel:
        cfm = _make_cfm({"fp-001": {"name": "A", "function_type": "EI"}})
        fp = cfm.functional_processes["fp-001"].model_copy(
            update={"metadata": {"source": "doc"}}
        )
        return cfm.model_copy(update={"functional_processes": {"fp-001": fp}})

    def test_element_exclusion_then_type_exclusion_continues(self) -> None:
        cfm = _make_cfm(
            {
                "fp-001": {"name": "A", "function_type": "EI"},
                "fp-002": {"name": "B", "function_type": "EQ"},
            }
        )
        result = mark_exclusions(cfm, {"EQ"}, {"fp-001"})
        assert result.functional_processes["fp-002"].metadata["excluded"] is True

    def test_blank_function_type_matched_exactly(self) -> None:
        result = mark_exclusions(self._cfm_without_function_type(), {""}, set())
        assert result.functional_processes["fp-001"].metadata["excluded"] is True

    def test_missing_function_type_not_matched_by_alien(self) -> None:
        result = mark_exclusions(self._cfm_without_function_type(), {"XXXX"}, set())
        assert result.functional_processes["fp-001"].metadata.get("excluded") is not True


class TestApplyComplexityOverrides:
    def test_applies_thresholds_and_rating(self) -> None:
        cfm = _make_cfm(
            {"fp-001": {"name": "A", "function_type": "EI", "det_count": "4", "ftr_count": "3"}}
        )
        overrides = [{"function_type": "EI", "thresholds": {"det": [2, 8], "ftr": [1, 5]}}]
        result = apply_complexity_overrides(cfm, overrides)
        md = result.functional_processes["fp-001"].metadata
        assert md["complexity_thresholds"] == {"det": [2, 8], "ftr": [1, 5]}
        assert md["complexity_source"] == "rule_pack_override"
        assert md["complexity_rating"] == "Average"

    def test_empty_function_type_skipped(self) -> None:
        cfm = _make_cfm({"fp-001": {"name": "A", "function_type": "EI"}})
        overrides = [{"function_type": "", "thresholds": {"det": [2, 8]}}]
        result = apply_complexity_overrides(cfm, overrides)
        assert "complexity_source" not in result.functional_processes["fp-001"].metadata

    def test_case_insensitive_match(self) -> None:
        cfm = _make_cfm({"fp-001": {"name": "A", "function_type": "ei"}})
        overrides = [{"function_type": "EI", "thresholds": {"det": [2, 8]}}]
        result = apply_complexity_overrides(cfm, overrides)
        assert result.functional_processes["fp-001"].metadata["complexity_source"] == "rule_pack_override"

    def test_unmatched_function_type(self) -> None:
        cfm = _make_cfm({"fp-001": {"name": "A", "function_type": "EO"}})
        overrides = [{"function_type": "EI", "thresholds": {"det": [2, 8]}}]
        result = apply_complexity_overrides(cfm, overrides)
        assert "complexity_source" not in result.functional_processes["fp-001"].metadata


class TestApplyWeightOverrides:
    def test_applies_weight(self) -> None:
        cfm = _make_cfm({"fp-001": {"name": "A", "function_type": "EI"}})
        fp = cfm.functional_processes["fp-001"].model_copy(
            update={"metadata": {**cfm.functional_processes["fp-001"].metadata, "complexity_rating": "High"}}
        )
        cfm = cfm.model_copy(update={"functional_processes": {"fp-001": fp}})
        overrides = [{"function_type": "EI", "complexity": "High", "weight": 5}]
        result = apply_weight_overrides(cfm, overrides)
        md = result.functional_processes["fp-001"].metadata
        assert md["ufp_weight"] == 5
        assert md["weight_source"] == "rule_pack_override"

    def test_non_matching_complexity_skipped(self) -> None:
        cfm = _make_cfm({"fp-001": {"name": "A", "function_type": "EI"}})
        fp = cfm.functional_processes["fp-001"].model_copy(
            update={"metadata": {**cfm.functional_processes["fp-001"].metadata, "complexity_rating": "High"}}
        )
        cfm = cfm.model_copy(update={"functional_processes": {"fp-001": fp}})
        overrides = [{"function_type": "EI", "complexity": "Low", "weight": 1}]
        result = apply_weight_overrides(cfm, overrides)
        assert "weight_source" not in result.functional_processes["fp-001"].metadata

    def test_incomplete_override_skipped(self) -> None:
        cfm = _make_cfm({"fp-001": {"name": "A", "function_type": "EI"}})
        overrides = [{"function_type": "EI", "complexity": "", "weight": 5}]
        result = apply_weight_overrides(cfm, overrides)
        assert "weight_source" not in result.functional_processes["fp-001"].metadata

    def test_missing_weight_skipped(self) -> None:
        cfm = _make_cfm({"fp-001": {"name": "A", "function_type": "EI"}})
        overrides = [{"function_type": "EI", "complexity": "High", "weight": None}]
        result = apply_weight_overrides(cfm, overrides)
        assert "weight_source" not in result.functional_processes["fp-001"].metadata

    def test_default_rating_used(self) -> None:
        cfm = _make_cfm({"fp-001": {"name": "A", "function_type": "EI"}})
        overrides = [{"function_type": "EI", "complexity": "Average", "weight": 3}]
        result = apply_weight_overrides(cfm, overrides)
        assert result.functional_processes["fp-001"].metadata["ufp_weight"] == 3

    def _cfm_with_rating(self, rating: str) -> CanonicalFunctionalModel:
        cfm = _make_cfm({"fp-001": {"name": "A", "function_type": "EI"}})
        fp = cfm.functional_processes["fp-001"].model_copy(
            update={
                "metadata": {
                    **cfm.functional_processes["fp-001"].metadata,
                    "complexity_rating": rating,
                }
            }
        )
        return cfm.model_copy(update={"functional_processes": {"fp-001": fp}})

    def test_weight_none_with_present_parts_not_applied(self) -> None:
        cfm = self._cfm_with_rating("High")
        overrides = [{"function_type": "EI", "complexity": "High", "weight": None}]
        result = apply_weight_overrides(cfm, overrides)
        assert "weight_source" not in result.functional_processes["fp-001"].metadata

    def test_blank_function_type_override_not_applied(self) -> None:
        cfm = self._cfm_with_rating("High")
        overrides = [{"function_type": "", "complexity": "High", "weight": 5}]
        result = apply_weight_overrides(cfm, overrides)
        assert "weight_source" not in result.functional_processes["fp-001"].metadata


class TestSetVaf:
    def test_sets_vaf(self) -> None:
        cfm = _make_cfm()
        result = set_vaf(cfm, 1.04)
        assert result.metadata.vaf == 1.04
        assert result is not cfm

    def test_preserves_existing_metadata(self) -> None:
        cfm = _make_cfm()
        result = set_vaf(cfm, 0.90)
        assert result.metadata.run_id == "test-run"
        assert result.metadata.vaf == 0.90