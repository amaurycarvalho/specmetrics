import pytest

from specmetrics.plugins.measurement.apf.plugin import APFMeasurementPlugin


class TestAPFMeasurementPlugin:
    def test_plugin_id(self):
        plugin = APFMeasurementPlugin()
        assert plugin.plugin_id() == "apf"

    def test_supported_methodology(self):
        plugin = APFMeasurementPlugin()
        assert "APF" in plugin.supported_methodology()

    def test_supported_function_types(self):
        plugin = APFMeasurementPlugin()
        types = plugin.supported_function_types()
        assert "ILF" in types
        assert "EIF" in types
        assert "EI" in types
        assert "EO" in types
        assert "EQ" in types
        assert len(types) == 5

    def test_measure_raises_on_none_cfm(self):
        plugin = APFMeasurementPlugin()
        with pytest.raises(ValueError, match="CFM input cannot be None"):
            plugin.measure(None)  # type: ignore[arg-type]
