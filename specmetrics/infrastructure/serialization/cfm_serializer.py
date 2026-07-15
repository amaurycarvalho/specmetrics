from __future__ import annotations

import json
import os
import tempfile
from typing import Any

from pydantic import ValidationError

from specmetrics.kernel.cfm.metadata import BuildMetadata, ClassificationConflict
from specmetrics.kernel.cfm.model import (
    Actor,
    BusinessRule,
    CanonicalFunctionalModel,
    DataGroup,
    EvidenceRef,
    FunctionalProcess,
    Operation,
    Relationship,
    UnclassifiedElement,
)


class InvalidCfmDataError(Exception):
    """Raised when CFM data is invalid or corrupted."""


class CfmSerializer:
    """Serialization for CanonicalFunctionalModel using JSON Lines format."""

    @staticmethod
    def save(cfm: CanonicalFunctionalModel, path: str) -> None:
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
                    for element_id, element in collection.items():
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
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise InvalidCfmDataError(f"Line {line_no}: invalid JSON — {exc}") from exc
                record_type = record.pop("type", None)
                if record_type == "metadata":
                    meta_record = record
                    run_id = record.get("run_id", "")
                    evidence_graph_ref = record.get("evidence_graph_ref", "")
                    meta_data = record.get("metadata", {})
                    if meta_data:
                        conflicts = [
                            ClassificationConflict(**c)
                            for c in meta_data.get("conflicts", [])
                        ]
                        metadata = BuildMetadata(
                            run_id=meta_data.get("run_id", run_id),
                            build_duration_ms=meta_data.get("build_duration_ms", 0),
                            element_counts=meta_data.get("element_counts", {}),
                            total_input_nodes=meta_data.get("total_input_nodes", 0),
                            unclassified_count=meta_data.get("unclassified_count", 0),
                            conflicts=conflicts,
                        )
                elif record_type == "actor":
                    try:
                        actor = Actor(**record)
                    except ValidationError as exc:
                        raise InvalidCfmDataError(f"Line {line_no}: invalid actor — {exc}") from exc
                    actors[actor.id] = actor
                elif record_type == "functional_process":
                    try:
                        fp = FunctionalProcess(**record)
                    except ValidationError as exc:
                        raise InvalidCfmDataError(f"Line {line_no}: invalid functional process — {exc}") from exc
                    functional_processes[fp.id] = fp
                elif record_type == "business_rule":
                    try:
                        br = BusinessRule(**record)
                    except ValidationError as exc:
                        raise InvalidCfmDataError(f"Line {line_no}: invalid business rule — {exc}") from exc
                    business_rules[br.id] = br
                elif record_type == "data_group":
                    try:
                        dg = DataGroup(**record)
                    except ValidationError as exc:
                        raise InvalidCfmDataError(f"Line {line_no}: invalid data group — {exc}") from exc
                    data_groups[dg.id] = dg
                elif record_type == "relationship":
                    try:
                        rel = Relationship(**record)
                    except ValidationError as exc:
                        raise InvalidCfmDataError(f"Line {line_no}: invalid relationship — {exc}") from exc
                    relationships.append(rel)
                elif record_type == "operation":
                    try:
                        op = Operation(**record)
                    except ValidationError as exc:
                        raise InvalidCfmDataError(f"Line {line_no}: invalid operation — {exc}") from exc
                    operations[op.id] = op
                elif record_type == "unclassified":
                    try:
                        ue = UnclassifiedElement(**record)
                    except ValidationError as exc:
                        raise InvalidCfmDataError(f"Line {line_no}: invalid unclassified element — {exc}") from exc
                    unclassified[ue.id] = ue
                else:
                    raise InvalidCfmDataError(f"Line {line_no}: unknown record type '{record_type}'")

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
