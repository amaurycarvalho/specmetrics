"""Serialization of the CanonicalFunctionalModel to JSON Lines format."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Callable
from typing import Any

from pydantic import ValidationError

from specmetrics.kernel.cfm.metadata import BuildMetadata, ClassificationConflict
from specmetrics.kernel.cfm.model import (
    Actor,
    BusinessRule,
    CanonicalFunctionalModel,
    DataGroup,
    FunctionalProcess,
    Operation,
    Relationship,
    UnclassifiedElement,
)

_ELEMENT_MODELS: dict[str, type] = {
    "actor": Actor,
    "functional_process": FunctionalProcess,
    "business_rule": BusinessRule,
    "data_group": DataGroup,
    "operation": Operation,
    "unclassified": UnclassifiedElement,
    "relationship": Relationship,
}


class InvalidCfmDataError(Exception):
    """Raised when CFM data is invalid or corrupted."""


class CfmSerializer:
    """Serialization for CanonicalFunctionalModel using JSON Lines format."""

    @staticmethod
    def save(cfm: CanonicalFunctionalModel, path: str) -> None:
        """Persist a canonical functional model to a JSON Lines file."""
        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(suffix=".jsonl", dir=dir_path or ".")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                meta = {
                    "type": "metadata",
                    "run_id": cfm.run_id,
                    "evidence_graph_ref": cfm.evidence_graph_ref,
                    "metadata": cfm.metadata.model_dump(mode="json"),
                }
                f.write(json.dumps(meta) + "\n")
                for element_type, collection in [
                    ("actor", cfm.actors),
                    ("functional_process", cfm.functional_processes),
                    ("business_rule", cfm.business_rules),
                    ("data_group", cfm.data_groups),
                    ("operation", cfm.operations),
                    ("unclassified", cfm.unclassified),
                ]:
                    for element in collection.values():
                        record = element.model_dump(mode="json")
                        record["type"] = element_type
                        f.write(json.dumps(record) + "\n")
                for rel in cfm.relationships:
                    record = rel.model_dump(mode="json")
                    record["type"] = "relationship"
                    f.write(json.dumps(record) + "\n")
            os.replace(tmp_path, path)
        except BaseException:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    @staticmethod
    def load(path: str) -> CanonicalFunctionalModel:
        """Load a canonical functional model from a JSON Lines file."""
        if not os.path.isfile(path):
            raise InvalidCfmDataError(f"File not found: {path}")
        meta_record: dict[str, Any] | None = None
        run_id = ""
        evidence_graph_ref = ""
        metadata = BuildMetadata(run_id="")
        actors: dict[str, Actor] = {}
        functional_processes: dict[str, FunctionalProcess] = {}
        business_rules: dict[str, BusinessRule] = {}
        data_groups: dict[str, DataGroup] = {}
        relationships: list[Relationship] = []
        operations: dict[str, Operation] = {}
        unclassified: dict[str, UnclassifiedElement] = {}

        with open(path, "r", encoding="utf-8") as f:
            stores = CfmSerializer._build_stores(
                actors,
                functional_processes,
                business_rules,
                data_groups,
                operations,
                unclassified,
                relationships,
            )
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise InvalidCfmDataError(
                        f"Line {line_no}: invalid JSON — {exc}"
                    ) from exc
                record_type = record.pop("type", None)
                if record_type == "metadata":
                    meta_record = record
                    run_id = record.get("run_id", "")
                    evidence_graph_ref = record.get("evidence_graph_ref", "")
                    metadata = CfmSerializer._build_metadata(record, run_id)
                    continue

                store = stores.get(record_type)
                if store is None:
                    raise InvalidCfmDataError(
                        f"Line {line_no}: unknown record type '{record_type}'"
                    )
                obj = CfmSerializer._parse_element(
                    record_type, record, line_no
                )
                store(obj)

        if meta_record is None:
            raise InvalidCfmDataError("Missing metadata record (first line)")

        return CanonicalFunctionalModel(
            run_id=run_id,
            actors=actors,
            functional_processes=functional_processes,
            business_rules=business_rules,
            data_groups=data_groups,
            relationships=relationships,
            operations=operations,
            unclassified=unclassified,
            metadata=metadata,
            evidence_graph_ref=evidence_graph_ref,
        )

    @staticmethod
    def _build_stores(
        actors: dict[str, Actor],
        functional_processes: dict[str, FunctionalProcess],
        business_rules: dict[str, BusinessRule],
        data_groups: dict[str, DataGroup],
        operations: dict[str, Operation],
        unclassified: dict[str, UnclassifiedElement],
        relationships: list[Relationship],
    ) -> dict[str, Callable[[Any], None]]:
        return {
            "actor": lambda o: actors.__setitem__(o.id, o),
            "functional_process": lambda o: functional_processes.__setitem__(o.id, o),
            "business_rule": lambda o: business_rules.__setitem__(o.id, o),
            "data_group": lambda o: data_groups.__setitem__(o.id, o),
            "operation": lambda o: operations.__setitem__(o.id, o),
            "unclassified": lambda o: unclassified.__setitem__(o.id, o),
            "relationship": relationships.append,
        }

    @staticmethod
    def _build_metadata(
        record: dict[str, Any], run_id: str
    ) -> BuildMetadata:
        meta_data = record.get("metadata", {})
        if not meta_data:
            return BuildMetadata(run_id=run_id)
        conflicts = [
            ClassificationConflict(**c) for c in meta_data.get("conflicts", [])
        ]
        return BuildMetadata(
            run_id=meta_data.get("run_id", run_id),
            build_duration_ms=meta_data.get("build_duration_ms", 0),
            element_counts=meta_data.get("element_counts", {}),
            total_input_nodes=meta_data.get("total_input_nodes", 0),
            unclassified_count=meta_data.get("unclassified_count", 0),
            conflicts=conflicts,
        )

    @staticmethod
    def _parse_element(
        record_type: str,
        record: dict[str, Any],
        line_no: int,
    ) -> object:
        model = _ELEMENT_MODELS.get(record_type)
        if model is None:
            raise InvalidCfmDataError(
                f"Line {line_no}: unknown record type '{record_type}'"
            )
        try:
            return model(**record)
        except ValidationError as exc:
            raise InvalidCfmDataError(
                f"Line {line_no}: invalid {record_type} — {exc}"
            ) from exc
