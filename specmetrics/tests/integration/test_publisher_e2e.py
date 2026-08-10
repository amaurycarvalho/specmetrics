from __future__ import annotations

from specmetrics.plugins.exporter.models import ExportMetadata, Measurement
from specmetrics.plugins.publisher.base import PublisherConfiguration
from specmetrics.plugins.publisher.otel_publisher import OTelPublisher


class TestPublisherE2E:
    def test_publisher_lifecycle(self) -> None:
        configs = [
            PublisherConfiguration(
                endpoint_url="http://localhost:4318",
                protocol="http",
                enabled=True,
                batch_interval_seconds=60,
                batch_max_size=100,
            )
        ]
        pub = OTelPublisher()
        pub.initialize(configs)
        pub.start()

        measurements = [
            Measurement(
                function_id="proc-1",
                function_name="Process Order",
                category="EI",
                complexity="Average",
                functional_size=4.0,
            )
        ]
        metadata = ExportMetadata(run_id="e2e-test", specmetrics_version="0.1.0")

        from specmetrics.plugins.publisher.base import PublisherConfig

        result = pub.publish(measurements, metadata, PublisherConfig())

        assert result.success is True
        assert result.metrics_count > 0

        statuses = pub.get_status()
        assert len(statuses) == 1
        assert statuses[0].endpoint_url == "http://localhost:4318"
        assert statuses[0].total_metrics_published == 0  # not yet flushed

        pub.stop()

    def test_multiple_endpoints(self) -> None:
        configs = [
            PublisherConfiguration(
                endpoint_url="http://endpoint-a:4318",
                protocol="http",
                enabled=True,
                batch_interval_seconds=60,
                batch_max_size=100,
            ),
            PublisherConfiguration(
                endpoint_url="http://endpoint-b:4318",
                protocol="http",
                enabled=True,
                batch_interval_seconds=60,
                batch_max_size=100,
            ),
        ]
        pub = OTelPublisher()
        pub.initialize(configs)
        pub.start()

        metadata = ExportMetadata(run_id="multi-ep-test")
        from specmetrics.plugins.publisher.base import PublisherConfig

        measurements = [
            Measurement(
                function_id="proc-1",
                function_name="Test",
                category="EI",
                functional_size=1.0,
            )
        ]
        result = pub.publish(measurements, metadata, PublisherConfig())
        assert result.success is True

        statuses = pub.get_status()
        assert len(statuses) == 2

        pub.stop()

    def test_disabled_endpoint_skipped(self) -> None:
        configs = [
            PublisherConfiguration(
                endpoint_url="http://enabled:4318",
                protocol="http",
                enabled=True,
                batch_interval_seconds=60,
            ),
            PublisherConfiguration(
                endpoint_url="http://disabled:4318",
                protocol="http",
                enabled=False,
                batch_interval_seconds=60,
            ),
        ]
        pub = OTelPublisher()
        pub.initialize(configs)
        assert len(pub._instances) == 1
        assert pub._instances[0].config.endpoint_url == "http://enabled:4318"
