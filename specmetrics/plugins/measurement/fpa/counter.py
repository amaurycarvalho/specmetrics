from __future__ import annotations

from typing import Optional
from uuid import uuid4

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel

from .complexity import (
    classify_data_function_complexity,
    classify_transactional_complexity,
    get_ufp_weight,
)
from .models import (
    FPAMeasurementResult,
    ComplexityDistributionRow,
    ComplexityRating,
    EvidenceRef,
    FunctionType,
    MeasuredFunction,
    MeasurementSummary,
    MeasurementWarning,
    TypeBreakdown,
)


class FPACounter:
    def count(
        self,
        cfm: CanonicalFunctionalModel,
        rule_pack_id: Optional[str] = None,
        weight_overrides: Optional[dict[str, dict[str, int]]] = None,
        excluded_types: Optional[list[FunctionType]] = None,
    ) -> FPAMeasurementResult:
        excluded = set(excluded_types or [])
        functions: list[MeasuredFunction] = []
        warnings: list[MeasurementWarning] = []

        for dg in cfm.data_groups.values():
            if dg.data_type == "external":
                ft: FunctionType = "EIF"
            else:
                ft = "ILF"

            if ft in excluded:
                continue

            det_count = 1
            if "det_count" in dg.metadata:
                det_count = int(dg.metadata["det_count"])

            ret_count = 1
            if "ret_count" in dg.metadata:
                ret_count = int(dg.metadata["ret_count"])
            elif dg.data_type == "external":
                ret_count = 1

            complexity = classify_data_function_complexity(ret_count, det_count)
            weight = get_ufp_weight(ft, complexity, weight_overrides)

            refs = [EvidenceRef(
                graph_node_id=dg.evidence.graph_node_id,
                document_id=dg.evidence.document_id,
                section_id=dg.evidence.section_id,
                text=dg.evidence.text,
            )]

            fn = MeasuredFunction(
                id=f"fn-{dg.id}",
                name=dg.name,
                function_type=ft,
                complexity=complexity,
                det_count=det_count,
                ret_count=ret_count,
                ufp_weight=weight,
                cfm_element_id=dg.id,
                cfm_element_type="DataGroup",
                evidence_refs=refs,
            )
            functions.append(fn)

        for op in cfm.operations.values():
            direction = op.metadata.get("direction", "")
            ft = self._classify_operation(direction)
            if ft is None:
                warnings.append(MeasurementWarning(
                    code="UNCLASSIFIED_OPERATION",
                    message=f"Operation '{op.name}' has no direction metadata; skipped",
                    cfm_element_id=op.id,
                ))
                continue

            if ft in excluded:
                continue

            det_count = 1
            if "det_count" in op.metadata:
                det_count = int(op.metadata["det_count"])

            ftr_count = 1
            if "ftr_count" in op.metadata:
                ftr_count = int(op.metadata["ftr_count"])
            else:
                ftr_count = len(cfm.data_groups)

            complexity = classify_transactional_complexity(ft, ftr_count, det_count)
            weight = get_ufp_weight(ft, complexity, weight_overrides)

            refs = [EvidenceRef(
                graph_node_id=op.evidence.graph_node_id,
                document_id=op.evidence.document_id,
                section_id=op.evidence.section_id,
                text=op.evidence.text,
            )]

            fn = MeasuredFunction(
                id=f"fn-{op.id}",
                name=op.name,
                function_type=ft,
                complexity=complexity,
                det_count=det_count,
                ftr_count=ftr_count,
                ufp_weight=weight,
                cfm_element_id=op.id,
                cfm_element_type="Operation",
                evidence_refs=refs,
            )
            functions.append(fn)

        summary = self._build_summary(functions)

        return FPAMeasurementResult(
            run_id=str(uuid4()),
            cfm_run_id=cfm.run_id,
            rule_pack_id=rule_pack_id,
            measured_functions=functions,
            summary=summary,
            warnings=warnings,
        )

    def _classify_operation(self, direction: str) -> Optional[FunctionType]:
        mapping = {
            "input": "EI",
            "output": "EO",
            "query": "EQ",
        }
        result = mapping.get(direction)
        return result  # type: ignore[return-value]

    def _build_summary(self, functions: list[MeasuredFunction]) -> MeasurementSummary:
        total_fp = sum(f.ufp_weight for f in functions)
        by_type: dict[FunctionType, TypeBreakdown] = {}
        by_complexity: dict[ComplexityRating, int] = {}
        dist: dict[tuple[FunctionType, ComplexityRating], list[int]] = {}

        for fn in functions:
            if fn.function_type not in by_type:
                by_type[fn.function_type] = TypeBreakdown(count=0, total_ufp=0)
            by_type[fn.function_type].count += 1
            by_type[fn.function_type].total_ufp += fn.ufp_weight

            if fn.complexity not in by_complexity:
                by_complexity[fn.complexity] = 0
            by_complexity[fn.complexity] += 1

            key = (fn.function_type, fn.complexity)
            if key not in dist:
                dist[key] = [0, 0]
            dist[key][0] += 1
            dist[key][1] += fn.ufp_weight

        complexity_distribution = [
            ComplexityDistributionRow(
                function_type=ft,
                complexity=cx,
                count=cnt,
                ufp_per_function=total // cnt if cnt > 0 else 0,
                total_ufp=total,
            )
            for (ft, cx), (cnt, total) in sorted(dist.items())
        ]

        return MeasurementSummary(
            total_function_count=len(functions),
            total_ufp=total_fp,
            by_type=by_type,
            by_complexity=by_complexity,
            complexity_distribution=complexity_distribution,
        )
