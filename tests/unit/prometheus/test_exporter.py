"""Unit tests for Prometheus exporter."""

from prometheus_client import generate_latest

from cow_performance.metrics.models import OrderMetadata, OrderStatus
from cow_performance.prometheus.exporter import PrometheusExporter


class TestPrometheusExporter:
    """Tests for PrometheusExporter class."""

    def test_default_port(self) -> None:
        """Test that default port is 9091."""
        exporter = PrometheusExporter()
        assert exporter.port == 9091

    def test_custom_port(self) -> None:
        """Test that custom port is used."""
        exporter = PrometheusExporter(port=9092)
        assert exporter.port == 9092

    def test_custom_scenario(self) -> None:
        """Test that custom scenario is used."""
        exporter = PrometheusExporter(scenario="stress-test")
        assert exporter.scenario == "stress-test"

    def test_is_running_initially_false(self) -> None:
        """Test that exporter is not running initially."""
        exporter = PrometheusExporter()
        assert exporter.is_running() is False

    def test_record_order_created(self) -> None:
        """Test manual order creation recording."""
        exporter = PrometheusExporter(scenario="test")
        exporter.record_order_created()

        output = generate_latest(exporter.registry).decode()
        assert 'cow_perf_orders_created_total{scenario="test"} 1.0' in output

    def test_record_order_submitted_with_latency(self) -> None:
        """Test order submission recording with latency."""
        exporter = PrometheusExporter(scenario="test")
        exporter.record_order_submitted(latency_seconds=0.25)

        output = generate_latest(exporter.registry).decode()
        assert 'cow_perf_orders_submitted_total{scenario="test"} 1.0' in output
        assert "cow_perf_submission_latency_seconds_sum" in output

    def test_record_order_filled_with_latencies(self) -> None:
        """Test order fill recording with latencies."""
        exporter = PrometheusExporter(scenario="test")
        exporter.record_order_filled(settlement_latency=30.0, lifecycle_latency=60.0)

        output = generate_latest(exporter.registry).decode()
        assert 'cow_perf_orders_filled_total{scenario="test"} 1.0' in output
        assert "cow_perf_settlement_latency_seconds_sum" in output
        assert "cow_perf_order_lifecycle_seconds_sum" in output

    def test_record_order_failed(self) -> None:
        """Test order failure recording."""
        exporter = PrometheusExporter(scenario="test")
        exporter.record_order_failed()

        output = generate_latest(exporter.registry).decode()
        assert 'cow_perf_orders_failed_total{scenario="test"} 1.0' in output

    def test_record_order_expired(self) -> None:
        """Test order expiration recording."""
        exporter = PrometheusExporter(scenario="test")
        exporter.record_order_expired()

        output = generate_latest(exporter.registry).decode()
        assert 'cow_perf_orders_expired_total{scenario="test"} 1.0' in output

    def test_update_active_orders(self) -> None:
        """Test active orders gauge update."""
        exporter = PrometheusExporter(scenario="test")
        exporter.update_active_orders(5)

        output = generate_latest(exporter.registry).decode()
        assert 'cow_perf_orders_active{scenario="test"} 5.0' in output

    def test_update_throughput(self) -> None:
        """Test throughput gauges update."""
        exporter = PrometheusExporter(scenario="test")
        exporter.update_throughput(
            orders_per_second=10.5,
            target_rate=15.0,
            actual_rate=10.5,
        )

        output = generate_latest(exporter.registry).decode()
        assert 'cow_perf_orders_per_second{scenario="test"} 10.5' in output
        assert 'cow_perf_target_rate{scenario="test"} 15.0' in output
        assert 'cow_perf_actual_rate{scenario="test"} 10.5' in output

    def test_set_test_info(self) -> None:
        """Test test info metric."""
        exporter = PrometheusExporter(scenario="test")
        exporter.set_test_info(test_id="abc123", git_commit="deadbeef", duration=300)

        output = generate_latest(exporter.registry).decode()
        assert "cow_perf_test_info" in output
        assert 'test_id="abc123"' in output
        assert 'scenario="test"' in output

    def test_set_test_duration(self) -> None:
        """Test test duration gauge."""
        exporter = PrometheusExporter(scenario="test")
        exporter.set_test_duration(300)

        output = generate_latest(exporter.registry).decode()
        assert 'cow_perf_test_duration_seconds{scenario="test"} 300.0' in output

    def test_set_num_traders(self) -> None:
        """Test num traders gauge."""
        exporter = PrometheusExporter(scenario="test")
        exporter.set_num_traders(10)

        output = generate_latest(exporter.registry).decode()
        assert 'cow_perf_num_traders{scenario="test"} 10.0' in output

    def test_update_progress(self) -> None:
        """Test progress percentage gauge."""
        exporter = PrometheusExporter(scenario="test")
        exporter.update_progress(75.0)

        output = generate_latest(exporter.registry).decode()
        assert 'cow_perf_test_progress_percent{scenario="test"} 75.0' in output


class TestPrometheusExporterOrderCallback:
    """Tests for PrometheusExporter order callback handling."""

    def test_callback_handles_created_status(self) -> None:
        """Test callback increments counter for CREATED status."""
        exporter = PrometheusExporter(scenario="test")

        order = OrderMetadata(
            order_uid="order-1",
            owner="0x123",
            creation_time=1000.0,
            current_status=OrderStatus.CREATED,
        )
        exporter._on_metric_update("order", order)

        output = generate_latest(exporter.registry).decode()
        assert 'cow_perf_orders_created_total{scenario="test"} 1.0' in output
        assert 'cow_perf_orders_active{scenario="test"} 1.0' in output

    def test_callback_handles_submitted_status(self) -> None:
        """Test callback increments counter and records latency for SUBMITTED."""
        exporter = PrometheusExporter(scenario="test")

        order = OrderMetadata(
            order_uid="order-1",
            owner="0x123",
            creation_time=1000.0,
            submission_time=1000.5,
            current_status=OrderStatus.SUBMITTED,
        )
        exporter._on_metric_update("order", order)

        output = generate_latest(exporter.registry).decode()
        assert 'cow_perf_orders_submitted_total{scenario="test"} 1.0' in output

    def test_callback_handles_filled_status(self) -> None:
        """Test callback increments counter and records latencies for FILLED."""
        exporter = PrometheusExporter(scenario="test")

        # First add as created to track in active orders
        order = OrderMetadata(
            order_uid="order-1",
            owner="0x123",
            creation_time=1000.0,
            current_status=OrderStatus.CREATED,
        )
        exporter._on_metric_update("order", order)

        # Then update to filled
        order.submission_time = 1000.5
        order.acceptance_time = 1001.0
        order.first_fill_time = 1030.0
        order.completion_time = 1030.0
        order.current_status = OrderStatus.FILLED
        exporter._on_metric_update("order", order)

        output = generate_latest(exporter.registry).decode()
        assert 'cow_perf_orders_filled_total{scenario="test"} 1.0' in output
        assert 'cow_perf_orders_active{scenario="test"} 0.0' in output

    def test_callback_handles_failed_status(self) -> None:
        """Test callback increments counter for FAILED status."""
        exporter = PrometheusExporter(scenario="test")

        # First add as created
        order = OrderMetadata(
            order_uid="order-1",
            owner="0x123",
            creation_time=1000.0,
            current_status=OrderStatus.CREATED,
        )
        exporter._on_metric_update("order", order)

        # Then update to failed
        order.current_status = OrderStatus.FAILED
        exporter._on_metric_update("order", order)

        output = generate_latest(exporter.registry).decode()
        assert 'cow_perf_orders_failed_total{scenario="test"} 1.0' in output
        assert 'cow_perf_orders_active{scenario="test"} 0.0' in output

    def test_callback_ignores_non_order_metrics(self) -> None:
        """Test callback ignores non-order metric types."""
        exporter = PrometheusExporter(scenario="test")

        # Should not raise
        exporter._on_metric_update("api", {"some": "data"})
        exporter._on_metric_update("resource", {"some": "data"})

        # Counters should still be at default
        output = generate_latest(exporter.registry).decode()
        # No increments should have happened
        assert "cow_perf_orders_created_total" in output
