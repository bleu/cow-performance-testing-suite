"""
Metrics collection framework for CoW Protocol performance testing.

This module provides data models, storage, and export functionality for
capturing and analyzing performance metrics during load testing.

Models:
    - OrderStatus: Order lifecycle states
    - OrderMetadata: Individual order tracking with timestamps
    - OrderMetrics: Aggregate order statistics (basic)
    - APIMetrics: HTTP request/response timing
    - ResourceSample: Point-in-time container resource snapshot
    - ResourceMetrics: Aggregated container resource metrics
    - TestRunMetrics: Complete test run summary

Storage:
    - MetricsStore: Thread-safe in-memory metrics storage
    - MetricsStoreConfig: Configuration for storage limits

Export:
    - export_store_to_json: Export full store to JSON
    - export_orders_to_csv: Export orders to CSV
    - export_api_metrics_to_csv: Export API metrics to CSV
    - save_metrics_to_file: Save to file with format selection
"""

from cow_performance.metrics.export import (
    api_metrics_to_dict,
    export_api_metrics_to_csv,
    export_orders_to_csv,
    export_store_to_json,
    order_metadata_to_dict,
    resource_metrics_to_dict,
    save_metrics_to_file,
    test_run_metrics_to_dict,
)
from cow_performance.metrics.models import (
    APIMetrics,
    OrderMetadata,
    OrderMetrics,
    OrderStatus,
    ResourceMetrics,
    ResourceSample,
    TestRunMetrics,
)
from cow_performance.metrics.store import MetricsStore, MetricsStoreConfig

__all__ = [
    # Models
    "OrderStatus",
    "OrderMetadata",
    "OrderMetrics",
    "APIMetrics",
    "ResourceSample",
    "ResourceMetrics",
    "TestRunMetrics",
    # Storage
    "MetricsStore",
    "MetricsStoreConfig",
    # Export
    "export_store_to_json",
    "export_orders_to_csv",
    "export_api_metrics_to_csv",
    "save_metrics_to_file",
    "order_metadata_to_dict",
    "api_metrics_to_dict",
    "resource_metrics_to_dict",
    "test_run_metrics_to_dict",
]
