import pytest

from specmetrics.plugins.measurement.apf.complexity import (
    classify_data_function_complexity,
    classify_transactional_complexity,
    get_ufp_weight,
)


class TestDataFunctionComplexity:
    def test_low_low_ilf(self):
        # 1 RET, 1-19 DETs → Low
        assert classify_data_function_complexity(1, 10) == "Low"
        assert classify_data_function_complexity(1, 19) == "Low"

    def test_low_average_ilf(self):
        # 2 RETs, 20-50 DETs → Average
        assert classify_data_function_complexity(2, 30) == "Average"

    def test_high_complexity_ilf(self):
        # 6+ RETs, 51+ DETs → High
        assert classify_data_function_complexity(6, 60) == "High"

    def test_low_on_boundary_ilf(self):
        assert classify_data_function_complexity(1, 1) == "Low"
        assert classify_data_function_complexity(2, 1) == "Low"

    def test_average_on_boundary_ilf(self):
        # 1 RET, 51+ DETs → Average
        assert classify_data_function_complexity(1, 51) == "Average"
        # 6 RETs, 1-19 DETs → Average
        assert classify_data_function_complexity(6, 10) == "Average"

    def test_high_on_boundary_ilf(self):
        assert classify_data_function_complexity(6, 51) == "High"
        assert classify_data_function_complexity(2, 51) == "High"
        assert classify_data_function_complexity(6, 20) == "High"


class TestTransactionalComplexityEI:
    def test_low_ei(self):
        # 0-1 FTRs, 1-4 DETs → Low
        assert classify_transactional_complexity("EI", 0, 3) == "Low"
        assert classify_transactional_complexity("EI", 1, 4) == "Low"

    def test_average_ei(self):
        # 2 FTRs, 5-15 DETs → Average
        assert classify_transactional_complexity("EI", 2, 10) == "Average"

    def test_high_ei(self):
        # 3+ FTRs, 16+ DETs → High
        assert classify_transactional_complexity("EI", 3, 20) == "High"


class TestTransactionalComplexityEO:
    def test_low_eo(self):
        assert classify_transactional_complexity("EO", 0, 4) == "Low"

    def test_average_eo(self):
        assert classify_transactional_complexity("EO", 2, 10) == "Average"

    def test_high_eo(self):
        assert classify_transactional_complexity("EO", 4, 20) == "High"


class TestTransactionalComplexityEQ:
    def test_low_eq(self):
        assert classify_transactional_complexity("EQ", 0, 4) == "Low"

    def test_average_eq(self):
        assert classify_transactional_complexity("EQ", 2, 10) == "Average"

    def test_high_eq(self):
        assert classify_transactional_complexity("EQ", 4, 20) == "High"


class TestUFPWeights:
    def test_ilf_weights(self):
        assert get_ufp_weight("ILF", "Low") == 7
        assert get_ufp_weight("ILF", "Average") == 10
        assert get_ufp_weight("ILF", "High") == 15

    def test_eif_weights(self):
        assert get_ufp_weight("EIF", "Low") == 5
        assert get_ufp_weight("EIF", "Average") == 7
        assert get_ufp_weight("EIF", "High") == 10

    def test_ei_weights(self):
        assert get_ufp_weight("EI", "Low") == 3
        assert get_ufp_weight("EI", "Average") == 4
        assert get_ufp_weight("EI", "High") == 6

    def test_eo_weights(self):
        assert get_ufp_weight("EO", "Low") == 4
        assert get_ufp_weight("EO", "Average") == 5
        assert get_ufp_weight("EO", "High") == 7

    def test_eq_weights(self):
        assert get_ufp_weight("EQ", "Low") == 3
        assert get_ufp_weight("EQ", "Average") == 4
        assert get_ufp_weight("EQ", "High") == 6

    def test_weight_override(self):
        overrides = {"ILF": {"Low": 99, "Average": 100, "High": 101}}
        assert get_ufp_weight("ILF", "Low", overrides) == 99
