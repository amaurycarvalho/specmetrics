from __future__ import annotations

from typing import Optional

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel

from .complexity import UFP_WEIGHTS
from .counter import APFCounter
from .explainer import MeasurementExplainer
from .models import APFMeasurementResult, RulePack


class APFMeasurementPlugin:
    def plugin_id(self) -> str:
        return "apf"

    def supported_methodology(self) -> str:
        return "IFPUG/APF Function Point Analysis"

    def supported_function_types(self) -> list[str]:
        return ["ILF", "EIF", "EI", "EO", "EQ"]

    def measure(
        self,
        cfm: CanonicalFunctionalModel,
        rule_pack: Optional[RulePack] = None,
    ) -> APFMeasurementResult:
        if cfm is None:
            raise ValueError("CFM input cannot be None")

        weight_overrides = None
        excluded_types = None
        rule_pack_id = None

        if rule_pack is not None:
            rule_pack_id = rule_pack.id
            if rule_pack.weight_overrides:
                merged = {}
                for ft in UFP_WEIGHTS:
                    merged[ft] = {
                        **UFP_WEIGHTS[ft],
                        **(rule_pack.weight_overrides.get(ft) or {}),
                    }
                weight_overrides = merged
            if rule_pack.excluded_types:
                excluded_types = rule_pack.excluded_types

        counter = APFCounter()
        result = counter.count(
            cfm,
            rule_pack_id=rule_pack_id,
            weight_overrides=weight_overrides,
            excluded_types=excluded_types,
        )

        explainer = MeasurementExplainer()
        result.explanations.extend(explainer.build_explanations(result))

        return result
