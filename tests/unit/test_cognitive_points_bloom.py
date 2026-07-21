from __future__ import annotations

from specmetrics.plugins.measurement.cognitive_points.bloom_classifier import (
    DefaultBloomClassifier,
)


class TestDefaultBloomClassifier:
    def test_decision_maps_to_evaluate(self):
        classifier = DefaultBloomClassifier()
        assert classifier.classify("decision") == "evaluate"

    def test_functional_process_maps_to_create(self):
        classifier = DefaultBloomClassifier()
        assert classifier.classify("functional_process") == "create"

    def test_glossary_term_maps_to_remember(self):
        classifier = DefaultBloomClassifier()
        assert classifier.classify("glossary_term") == "remember"

    def test_exploration_maps_to_understand(self):
        classifier = DefaultBloomClassifier()
        assert classifier.classify("exploration") == "understand"

    def test_clarification_maps_to_analyze(self):
        classifier = DefaultBloomClassifier()
        assert classifier.classify("clarification") == "analyze"

    def test_unknown_type_uses_default(self):
        classifier = DefaultBloomClassifier()
        assert classifier.classify("unknown_type") == "understand"

    def test_custom_default_level(self):
        classifier = DefaultBloomClassifier(default_bloom_level="remember")
        assert classifier.classify("unknown") == "remember"

    def test_custom_mapping_overrides_default(self):
        classifier = DefaultBloomClassifier(bloom_mappings={"decision": "remember"})
        assert classifier.classify("decision") == "remember"

    def test_custom_mapping_adds_new_types(self):
        classifier = DefaultBloomClassifier(bloom_mappings={"custom_type": "create"})
        assert classifier.classify("custom_type") == "create"

    def test_default_weights(self):
        classifier = DefaultBloomClassifier()
        assert classifier.get_weight("remember") == 1.0
        assert classifier.get_weight("understand") == 2.0
        assert classifier.get_weight("apply") == 3.0
        assert classifier.get_weight("analyze") == 4.0
        assert classifier.get_weight("evaluate") == 5.0
        assert classifier.get_weight("create") == 8.0
        assert classifier.get_weight("unknown") == 1.0

    def test_custom_weights(self):
        classifier = DefaultBloomClassifier(
            bloom_weights={"remember": 0.5, "create": 10.0}
        )
        assert classifier.get_weight("remember") == 0.5
        assert classifier.get_weight("create") == 10.0
        assert classifier.get_weight("analyze") == 4.0


class TestDefaultBloomClassifierMappings:
    def test_all_default_mappings(self):
        classifier = DefaultBloomClassifier()
        expected = {
            "exploration": "understand",
            "clarification": "analyze",
            "refinement": "apply",
            "review": "evaluate",
            "validation": "evaluate",
            "decision": "evaluate",
            "assumption": "understand",
            "constraint": "apply",
            "risk": "analyze",
            "open_question": "analyze",
            "acceptance_criterion": "apply",
            "glossary_term": "remember",
            "functional_process": "create",
            "business_rule": "apply",
            "operation": "apply",
            "data_group": "understand",
            "relationship": "understand",
            "actor": "remember",
        }
        for element_type, expected_level in expected.items():
            actual = classifier.classify(element_type)
            assert actual == expected_level, (
                f"{element_type} should map to {expected_level}, got {actual}"
            )

    def test_mappings_immutable(self):
        classifier = DefaultBloomClassifier()
        mappings = classifier.mappings
        mappings["test"] = "create"
        assert "test" not in classifier.mappings
