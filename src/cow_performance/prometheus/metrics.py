"""Prometheus metric definitions for CoW Protocol performance testing.

All metrics are prefixed with `cow_perf_` to distinguish from production metrics.
Uses a custom CollectorRegistry to avoid conflicts during testing.
"""

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Info,
)


class MetricsRegistry:
    """
    Registry of Prometheus metrics for performance testing.

    Uses a custom CollectorRegistry to avoid conflicts with the default registry.
    All metrics are prefixed with `cow_perf_` as per naming convention.

    Example:
        registry = MetricsRegistry()
        registry.orders_created.labels(scenario="stress").inc()
    """

    def __init__(self, registry: CollectorRegistry | None = None):
        """
        Initialize the metrics registry.

        Args:
            registry: Optional custom registry. Creates new one if not provided.
        """
        self.registry = registry or CollectorRegistry()
        self._init_order_metrics()
        self._init_latency_metrics()
        self._init_throughput_metrics()
        self._init_test_metadata()

    def _init_order_metrics(self) -> None:
        """Initialize order-related counters and gauges."""
        # Counters for order lifecycle events
        self.orders_created = Counter(
            "cow_perf_orders_created_total",
            "Total number of orders created",
            ["scenario"],
            registry=self.registry,
        )
        self.orders_submitted = Counter(
            "cow_perf_orders_submitted_total",
            "Total number of orders submitted to API",
            ["scenario"],
            registry=self.registry,
        )
        self.orders_filled = Counter(
            "cow_perf_orders_filled_total",
            "Total number of orders successfully filled",
            ["scenario"],
            registry=self.registry,
        )
        self.orders_failed = Counter(
            "cow_perf_orders_failed_total",
            "Total number of orders that failed",
            ["scenario"],
            registry=self.registry,
        )
        self.orders_expired = Counter(
            "cow_perf_orders_expired_total",
            "Total number of orders that expired",
            ["scenario"],
            registry=self.registry,
        )

        # Gauge for active orders
        self.orders_active = Gauge(
            "cow_perf_orders_active",
            "Currently active (non-terminal) orders",
            ["scenario"],
            registry=self.registry,
        )

    def _init_latency_metrics(self) -> None:
        """Initialize latency histograms with appropriate buckets."""
        # Submission latency (fast operation: creation to submission)
        self.submission_latency = Histogram(
            "cow_perf_submission_latency_seconds",
            "Time from order creation to API submission",
            ["scenario"],
            buckets=[0.1, 0.5, 1, 2, 5, 10, 30],
            registry=self.registry,
        )

        # Orderbook acceptance latency (submission to acceptance)
        self.orderbook_latency = Histogram(
            "cow_perf_orderbook_latency_seconds",
            "Time from submission to orderbook acceptance",
            ["scenario"],
            buckets=[0.1, 0.5, 1, 2, 5, 10, 30],
            registry=self.registry,
        )

        # Settlement latency (slow operation: acceptance to fill)
        self.settlement_latency = Histogram(
            "cow_perf_settlement_latency_seconds",
            "Time from acceptance to order fill",
            ["scenario"],
            buckets=[10, 30, 60, 120, 300, 600],
            registry=self.registry,
        )

        # Full lifecycle (creation to completion)
        self.order_lifecycle = Histogram(
            "cow_perf_order_lifecycle_seconds",
            "Total order lifecycle duration (creation to completion)",
            ["scenario"],
            buckets=[10, 30, 60, 120, 300, 600, 900],
            registry=self.registry,
        )

    def _init_throughput_metrics(self) -> None:
        """Initialize throughput gauges."""
        self.orders_per_second = Gauge(
            "cow_perf_orders_per_second",
            "Current order submission rate",
            ["scenario"],
            registry=self.registry,
        )
        self.target_rate = Gauge(
            "cow_perf_target_rate",
            "Configured target submission rate",
            ["scenario"],
            registry=self.registry,
        )
        self.actual_rate = Gauge(
            "cow_perf_actual_rate",
            "Measured actual submission rate",
            ["scenario"],
            registry=self.registry,
        )

    def _init_test_metadata(self) -> None:
        """Initialize test metadata metrics."""
        self.test_info = Info(
            "cow_perf_test",
            "Performance test information",
            registry=self.registry,
        )
        self.test_start_timestamp = Gauge(
            "cow_perf_test_start_timestamp",
            "Test start Unix timestamp",
            ["scenario"],
            registry=self.registry,
        )
        self.test_duration_seconds = Gauge(
            "cow_perf_test_duration_seconds",
            "Configured test duration in seconds",
            ["scenario"],
            registry=self.registry,
        )
        self.num_traders = Gauge(
            "cow_perf_num_traders",
            "Number of simulated traders",
            ["scenario"],
            registry=self.registry,
        )
        self.test_progress_percent = Gauge(
            "cow_perf_test_progress_percent",
            "Test completion percentage (0-100)",
            ["scenario"],
            registry=self.registry,
        )
