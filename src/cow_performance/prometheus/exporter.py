"""Prometheus HTTP exporter for CoW Protocol performance testing metrics.

Exposes metrics at /metrics endpoint for Prometheus scraping.
Integrates with MetricsStore via callbacks for real-time updates.
"""

import logging
import platform
import time
from typing import TYPE_CHECKING

from prometheus_client import CollectorRegistry, start_http_server

from cow_performance import __version__
from cow_performance.metrics.models import OrderMetadata, OrderStatus
from cow_performance.prometheus.metrics import MetricsRegistry

if TYPE_CHECKING:
    from cow_performance.metrics.store import MetricsStore

logger = logging.getLogger(__name__)


class PrometheusExporter:
    """
    Prometheus HTTP exporter for performance testing.

    Exposes metrics at /metrics endpoint for Prometheus scraping.
    Integrates with MetricsStore via callbacks for real-time updates.

    Example:
        exporter = PrometheusExporter(port=9091, scenario="stress-test")
        exporter.start()

        # Register with MetricsStore for real-time updates
        exporter.register_with_store(metrics_store)

        # ... run tests ...

        exporter.stop()
    """

    DEFAULT_PORT = 9091

    def __init__(
        self,
        port: int = DEFAULT_PORT,
        scenario: str = "default",
    ):
        """
        Initialize the Prometheus exporter.

        Args:
            port: Port for HTTP server (default: 9091)
            scenario: Scenario name for metric labels
        """
        self.port = port
        self.scenario = scenario
        self._metrics = MetricsRegistry()
        self._running = False
        self._store: MetricsStore | None = None
        self._active_orders: set[str] = set()

    @property
    def registry(self) -> CollectorRegistry:
        """Get the Prometheus CollectorRegistry."""
        return self._metrics.registry

    def start(self) -> None:
        """Start the HTTP server for metrics exposition."""
        if self._running:
            logger.warning("Prometheus exporter already running on port %d", self.port)
            return

        try:
            start_http_server(self.port, registry=self._metrics.registry)
            self._running = True
            logger.info("Prometheus exporter started on port %d", self.port)
        except OSError as e:
            logger.error("Failed to start Prometheus exporter on port %d: %s", self.port, e)
            raise

    def stop(self) -> None:
        """Stop the exporter and unregister callbacks."""
        if not self._running:
            return

        # Unregister from MetricsStore if registered
        if self._store is not None:
            self._store.unregister_callback(self._on_metric_update)
            self._store = None

        self._running = False
        logger.info("Prometheus exporter stopped")

    def register_with_store(self, store: "MetricsStore") -> None:
        """
        Register with MetricsStore for real-time metric updates.

        Args:
            store: The MetricsStore to receive updates from
        """
        self._store = store
        store.register_callback(self._on_metric_update)
        logger.debug("Prometheus exporter registered with MetricsStore")

    def _on_metric_update(self, metric_type: str, metric: object) -> None:
        """
        Callback for MetricsStore updates.

        Maps incoming metrics to Prometheus metrics based on type.
        """
        try:
            if metric_type == "order" and isinstance(metric, OrderMetadata):
                self._update_order_metrics(metric)
            # API and resource metrics will be handled in Phase 2
        except Exception as e:
            logger.warning("Error updating Prometheus metric: %s", e)

    def _update_order_metrics(self, order: OrderMetadata) -> None:
        """Update order-related Prometheus metrics from OrderMetadata."""
        status = order.current_status
        scenario = self.scenario

        # Track active orders
        if status == OrderStatus.CREATED:
            self._metrics.orders_created.labels(scenario=scenario).inc()
            self._active_orders.add(order.order_uid)

        elif status == OrderStatus.SUBMITTED:
            self._metrics.orders_submitted.labels(scenario=scenario).inc()

            # Record submission latency if available
            latency = order.get_time_to_submit()
            if latency is not None:
                self._metrics.submission_latency.labels(scenario=scenario).observe(latency)

        elif status in (OrderStatus.ACCEPTED, OrderStatus.OPEN):
            # Record orderbook acceptance latency
            latency = order.get_time_to_accept()
            if latency is not None:
                self._metrics.orderbook_latency.labels(scenario=scenario).observe(latency)

        elif status == OrderStatus.FILLED:
            self._metrics.orders_filled.labels(scenario=scenario).inc()
            self._active_orders.discard(order.order_uid)

            # Record settlement latency (acceptance to fill)
            latency = order.get_time_to_fill()
            if latency is not None:
                self._metrics.settlement_latency.labels(scenario=scenario).observe(latency)

            # Record full lifecycle
            lifecycle = order.get_total_lifecycle_time()
            if lifecycle is not None:
                self._metrics.order_lifecycle.labels(scenario=scenario).observe(lifecycle)

        elif status == OrderStatus.FAILED:
            self._metrics.orders_failed.labels(scenario=scenario).inc()
            self._active_orders.discard(order.order_uid)

        elif status == OrderStatus.EXPIRED:
            self._metrics.orders_expired.labels(scenario=scenario).inc()
            self._active_orders.discard(order.order_uid)

        elif status == OrderStatus.CANCELLED:
            # Cancelled orders are tracked but not counted as failed
            self._active_orders.discard(order.order_uid)

        # Update active orders gauge
        self._metrics.orders_active.labels(scenario=scenario).set(len(self._active_orders))

    # --- Manual Recording Methods (for direct updates) ---

    def record_order_created(self) -> None:
        """Record an order creation event."""
        self._metrics.orders_created.labels(scenario=self.scenario).inc()

    def record_order_submitted(self, latency_seconds: float | None = None) -> None:
        """Record an order submission with optional latency."""
        self._metrics.orders_submitted.labels(scenario=self.scenario).inc()
        if latency_seconds is not None:
            self._metrics.submission_latency.labels(scenario=self.scenario).observe(latency_seconds)

    def record_order_filled(
        self,
        settlement_latency: float | None = None,
        lifecycle_latency: float | None = None,
    ) -> None:
        """Record an order fill with optional latencies."""
        self._metrics.orders_filled.labels(scenario=self.scenario).inc()
        if settlement_latency is not None:
            self._metrics.settlement_latency.labels(scenario=self.scenario).observe(
                settlement_latency
            )
        if lifecycle_latency is not None:
            self._metrics.order_lifecycle.labels(scenario=self.scenario).observe(lifecycle_latency)

    def record_order_failed(self) -> None:
        """Record an order failure."""
        self._metrics.orders_failed.labels(scenario=self.scenario).inc()

    def record_order_expired(self) -> None:
        """Record an order expiration."""
        self._metrics.orders_expired.labels(scenario=self.scenario).inc()

    def update_active_orders(self, count: int) -> None:
        """Update the active orders gauge."""
        self._metrics.orders_active.labels(scenario=self.scenario).set(count)

    def update_throughput(
        self,
        orders_per_second: float,
        target_rate: float | None = None,
        actual_rate: float | None = None,
    ) -> None:
        """Update throughput gauges."""
        self._metrics.orders_per_second.labels(scenario=self.scenario).set(orders_per_second)
        if target_rate is not None:
            self._metrics.target_rate.labels(scenario=self.scenario).set(target_rate)
        if actual_rate is not None:
            self._metrics.actual_rate.labels(scenario=self.scenario).set(actual_rate)

    def set_test_info(
        self,
        test_id: str,
        git_commit: str = "",
        duration: int = 0,
    ) -> None:
        """Set test metadata info metric."""
        self._metrics.test_info.info(
            {
                "test_id": test_id,
                "scenario": self.scenario,
                "git_commit": git_commit,
                "duration": str(duration),
                "python_version": platform.python_version(),
                "platform": platform.system(),
                "cow_perf_version": __version__,
            }
        )

    def set_test_start(self, timestamp: float | None = None) -> None:
        """Set test start timestamp."""
        ts = timestamp or time.time()
        self._metrics.test_start_timestamp.labels(scenario=self.scenario).set(ts)

    def set_test_duration(self, duration_seconds: int) -> None:
        """Set configured test duration."""
        self._metrics.test_duration_seconds.labels(scenario=self.scenario).set(duration_seconds)

    def set_num_traders(self, count: int) -> None:
        """Set number of simulated traders."""
        self._metrics.num_traders.labels(scenario=self.scenario).set(count)

    def update_progress(self, percent: float) -> None:
        """Update test progress percentage (0-100)."""
        self._metrics.test_progress_percent.labels(scenario=self.scenario).set(percent)

    def is_running(self) -> bool:
        """Check if exporter is running."""
        return self._running
