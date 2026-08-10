from __future__ import annotations

from typing import ClassVar

from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.plugins.measurement.tshirt._extractors import _ItemExtractionMixin


class _Result:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class TestExtractSpItems:
    def test_none_returns_none(self):
        assert _ItemExtractionMixin()._extract_sp_items(None) is None

    def test_dict_storypoints_entities(self):
        out = _ItemExtractionMixin()._extract_sp_items(
            {"storypoints_entities": [1, 2]}
        )
        assert out == [1, 2]

    def test_dict_items(self):
        out = _ItemExtractionMixin()._extract_sp_items({"items": ["a"]})
        assert out == ["a"]

    def test_dict_estimated_items(self):
        out = _ItemExtractionMixin()._extract_sp_items({"estimated_items": ["b"]})
        assert out == ["b"]

    def test_object_with_items(self):
        out = _ItemExtractionMixin()._extract_sp_items(_Result(items=[3]))
        assert out == [3]

    def test_object_without_items_returns_none(self):
        assert _ItemExtractionMixin()._extract_sp_items(_Result(x=1)) is None


class TestExtractRunId:
    def test_none_returns_none(self):
        assert _ItemExtractionMixin()._extract_run_id(None) is None

    def test_dict_run_id(self):
        assert _ItemExtractionMixin()._extract_run_id({"run_id": "r1"}) == "r1"

    def test_dict_storypoints_run_id(self):
        assert _ItemExtractionMixin()._extract_run_id(
            {"storypoints_run_id": "r2"}
        ) == "r2"

    def test_dict_execution_id(self):
        assert _ItemExtractionMixin()._extract_run_id({"execution_id": "r3"}) == "r3"

    def test_object_with_run_id(self):
        assert _ItemExtractionMixin()._extract_run_id(_Result(run_id="r4")) == "r4"

    def test_object_without_run_id_returns_none(self):
        assert _ItemExtractionMixin()._extract_run_id(_Result(x=1)) is None


class TestGetSpValue:
    def test_dict_normalized_value(self):
        assert _ItemExtractionMixin()._get_sp_value({"normalized_value": 5}) == 5

    def test_dict_story_point_value(self):
        assert _ItemExtractionMixin()._get_sp_value({"story_point_value": 6}) == 6

    def test_dict_value(self):
        assert _ItemExtractionMixin()._get_sp_value({"value": 7}) == 7

    def test_dict_missing_value(self):
        assert _ItemExtractionMixin()._get_sp_value({"other": 1}) is None

    def test_object_normalized_value(self):
        assert _ItemExtractionMixin()._get_sp_value(_Result(normalized_value=8)) == 8

    def test_object_story_point_value(self):
        assert _ItemExtractionMixin()._get_sp_value(_Result(story_point_value=9)) == 9

    def test_object_value(self):
        assert _ItemExtractionMixin()._get_sp_value(_Result(value=10)) == 10

    def test_object_missing_value(self):
        assert _ItemExtractionMixin()._get_sp_value(_Result(x=1)) is None


class TestGetElemId:
    def test_dict(self):
        assert _ItemExtractionMixin()._get_elem_id({"element_id": "f1"}) == "f1"

    def test_dict_missing_defaults_empty(self):
        assert _ItemExtractionMixin()._get_elem_id({}) == ""

    def test_object(self):
        assert _ItemExtractionMixin()._get_elem_id(_Result(element_id="f2")) == "f2"


class TestGetElemName:
    def test_dict(self):
        assert _ItemExtractionMixin()._get_elem_name({"element_name": "n1"}) == "n1"

    def test_dict_missing_defaults_empty(self):
        assert _ItemExtractionMixin()._get_elem_name({}) == ""

    def test_object(self):
        assert _ItemExtractionMixin()._get_elem_name(_Result(element_name="n2")) == "n2"


class TestResolveMappingOverride:
    def test_metadata_none_returns_none(self):
        ctx = PipelineContext(metadata=None)
        assert _ItemExtractionMixin()._resolve_mapping_override(ctx) is None

    def test_dict_metadata_with_mapping(self):
        ctx = PipelineContext(
            metadata={
                "tshirt_mapping": [
                    {"label": "S", "story_point_range": [1, 3]},
                    {"label": "M", "story_point_range": [4, 8], "ordinal": 2},
                ]
            }
        )
        sizes = _ItemExtractionMixin()._resolve_mapping_override(ctx)
        assert sizes is not None
        assert sizes[0].label == "S"
        assert sizes[0].story_point_range == (1, 3)
        assert sizes[0].ordinal == 1
        assert sizes[1].label == "M"
        assert sizes[1].ordinal == 2

    def test_dict_metadata_without_mapping(self):
        ctx = PipelineContext(metadata={"other": 1})
        assert _ItemExtractionMixin()._resolve_mapping_override(ctx) is None

    def test_object_metadata_with_extra(self):
        ctx = PipelineContext(
            metadata=_Result(
                extra={
                    "tshirt_mapping": [
                        {"label": "L", "story_point_range": [9, 13]}
                    ]
                }
            )
        )
        sizes = _ItemExtractionMixin()._resolve_mapping_override(ctx)
        assert sizes[0].label == "L"
        assert sizes[0].story_point_range == (9, 13)

    def test_object_metadata_without_extra(self):
        ctx = PipelineContext(metadata=_Result(x=1))
        assert _ItemExtractionMixin()._resolve_mapping_override(ctx) is None

    def test_object_metadata_extra_empty(self):
        ctx = PipelineContext(metadata=_Result(extra={}))
        assert _ItemExtractionMixin()._resolve_mapping_override(ctx) is None


class TestDefaultMappingFallback:
    def test_mapping_override_precedence_over_default(self):
        class Ctx:
            metadata: ClassVar = {
                "tshirt_mapping": [
                    {"label": "TINY", "story_point_range": [1, 100], "ordinal": 1}
                ]
            }

        ctx = PipelineContext(metadata=Ctx.metadata)
        sizes = _ItemExtractionMixin()._resolve_mapping_override(ctx)
        assert sizes[0].label == "TINY"