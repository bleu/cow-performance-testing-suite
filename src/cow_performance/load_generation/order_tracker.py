"""
Order tracking and lifecycle monitoring for CoW Protocol orders.

This module provides functionality to track order states, monitor lifecycle
transitions, and calculate order metrics for performance analysis.
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class OrderStatus(str, Enum):
    """Order lifecycle states."""

    CREATED = "created"  # Order created locally, not yet submitted
    SUBMITTED = "submitted"  # Order submitted to API, awaiting confirmation
    ACCEPTED = "accepted"  # Order accepted by orderbook
    OPEN = "open"  # Order is active in the orderbook
    FILLED = "filled"  # Order fully filled
    PARTIALLY_FILLED = "partiallyFilled"  # Order partially filled
    EXPIRED = "expired"  # Order expired (past validTo)
    CANCELLED = "cancelled"  # Order cancelled by user
    FAILED = "failed"  # Order submission/processing failed


@dataclass
class OrderMetadata:
    """
    Metadata about an order for tracking and metrics.

    Tracks timestamps, status transitions, and order details for
    lifecycle analysis and performance monitoring.
    """

    order_uid: str
    owner: str
    creation_time: float
    submission_time: float | None = None
    acceptance_time: float | None = None
    first_fill_time: float | None = None
    completion_time: float | None = None

    current_status: OrderStatus = OrderStatus.CREATED
    status_history: list[tuple[float, OrderStatus]] = field(default_factory=list)

    sell_token: str = ""
    buy_token: str = ""
    sell_amount: str = "0"
    buy_amount: str = "0"

    filled_amount: str = "0"
    error_message: str | None = None

    def update_status(self, new_status: OrderStatus, timestamp: float | None = None) -> None:
        """
        Update order status and record the transition.

        Args:
            new_status: The new order status
            timestamp: Optional timestamp (uses current time if not provided)
        """
        if timestamp is None:
            timestamp = time.time()

        self.current_status = new_status
        self.status_history.append((timestamp, new_status))

        # Update lifecycle timestamps
        if new_status == OrderStatus.SUBMITTED and self.submission_time is None:
            self.submission_time = timestamp
        elif (
            new_status in (OrderStatus.ACCEPTED, OrderStatus.OPEN) and self.acceptance_time is None
        ):
            self.acceptance_time = timestamp

        # Handle fill time (can be both FILLED and completion)
        if (
            new_status in (OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED)
            and self.first_fill_time is None
        ):
            self.first_fill_time = timestamp

        # Handle completion (terminal states)
        if new_status in (
            OrderStatus.FILLED,
            OrderStatus.EXPIRED,
            OrderStatus.CANCELLED,
            OrderStatus.FAILED,
        ):
            if self.completion_time is None:
                self.completion_time = timestamp

    def get_time_to_submit(self) -> float | None:
        """Get time from creation to submission in seconds."""
        if self.submission_time is None:
            return None
        return self.submission_time - self.creation_time

    def get_time_to_accept(self) -> float | None:
        """Get time from submission to acceptance in seconds."""
        if self.submission_time is None or self.acceptance_time is None:
            return None
        return self.acceptance_time - self.submission_time

    def get_time_to_fill(self) -> float | None:
        """Get time from acceptance to first fill in seconds."""
        if self.acceptance_time is None or self.first_fill_time is None:
            return None
        return self.first_fill_time - self.acceptance_time

    def get_total_lifecycle_time(self) -> float | None:
        """Get total time from creation to completion in seconds."""
        if self.completion_time is None:
            return None
        return self.completion_time - self.creation_time

    def is_terminal_state(self) -> bool:
        """Check if order is in a terminal state (no more updates expected)."""
        return self.current_status in (
            OrderStatus.FILLED,
            OrderStatus.EXPIRED,
            OrderStatus.CANCELLED,
            OrderStatus.FAILED,
        )


@dataclass
class OrderMetrics:
    """
    Aggregated metrics for order tracking.

    Provides summary statistics for order lifecycle performance
    across multiple orders.
    """

    total_orders: int = 0
    orders_created: int = 0
    orders_submitted: int = 0
    orders_accepted: int = 0
    orders_filled: int = 0
    orders_partially_filled: int = 0
    orders_expired: int = 0
    orders_cancelled: int = 0
    orders_failed: int = 0

    avg_time_to_submit: float = 0.0
    avg_time_to_accept: float = 0.0
    avg_time_to_fill: float = 0.0
    avg_total_lifecycle_time: float = 0.0


class OrderTracker:
    """
    Tracks order lifecycle and monitors status changes.

    This class maintains order metadata, polls order status from the API,
    and calculates performance metrics for load testing analysis.
    """

    def __init__(self, poll_interval: float = 5.0, max_poll_attempts: int = 60):
        """
        Initialize the order tracker.

        Args:
            poll_interval: Seconds between status polls (default 5.0)
            max_poll_attempts: Maximum number of poll attempts before giving up (default 60)
        """
        self.poll_interval = poll_interval
        self.max_poll_attempts = max_poll_attempts
        self._orders: dict[str, OrderMetadata] = {}
        self._polling_tasks: dict[str, asyncio.Task] = {}

    def track_order(
        self,
        order_uid: str,
        owner: str,
        sell_token: str = "",
        buy_token: str = "",
        sell_amount: str = "0",
        buy_amount: str = "0",
    ) -> OrderMetadata:
        """
        Start tracking a new order.

        Args:
            order_uid: Unique identifier for the order
            owner: Address of the order owner
            sell_token: Address of sell token
            buy_token: Address of buy token
            sell_amount: Amount being sold
            buy_amount: Amount being bought

        Returns:
            The OrderMetadata instance for this order
        """
        metadata = OrderMetadata(
            order_uid=order_uid,
            owner=owner,
            creation_time=time.time(),
            sell_token=sell_token,
            buy_token=buy_token,
            sell_amount=sell_amount,
            buy_amount=buy_amount,
        )
        self._orders[order_uid] = metadata
        return metadata

    def get_order(self, order_uid: str) -> OrderMetadata | None:
        """
        Get metadata for a tracked order.

        Args:
            order_uid: The order UID to retrieve

        Returns:
            OrderMetadata if found, None otherwise
        """
        return self._orders.get(order_uid)

    def get_all_orders(self) -> list[OrderMetadata]:
        """
        Get all tracked orders.

        Returns:
            List of all OrderMetadata instances
        """
        return list(self._orders.values())

    def update_order_status(
        self,
        order_uid: str,
        new_status: OrderStatus,
        filled_amount: str | None = None,
        error_message: str | None = None,
    ) -> None:
        """
        Update the status of a tracked order.

        Args:
            order_uid: The order UID to update
            new_status: The new status
            filled_amount: Optional filled amount for partial/full fills
            error_message: Optional error message for failed orders
        """
        if order_uid not in self._orders:
            return

        metadata = self._orders[order_uid]
        metadata.update_status(new_status)

        if filled_amount is not None:
            metadata.filled_amount = filled_amount
        if error_message is not None:
            metadata.error_message = error_message

    async def poll_order_status(
        self,
        order_uid: str,
        api_client: Any,  # Type would be the API client class
    ) -> OrderStatus:
        """
        Poll order status from the API.

        Fetches the current order status from the orderbook API and maps it
        to our internal OrderStatus enum.

        Args:
            order_uid: The order UID to poll
            api_client: The API client to use for polling

        Returns:
            The current order status
        """
        metadata = self.get_order(order_uid)
        if metadata is None:
            return OrderStatus.FAILED

        # If no API client provided, return current status (dry-run mode)
        if api_client is None:
            return metadata.current_status

        try:
            # Fetch order details from API
            order_response = await api_client.get_order(order_uid)
            api_status = order_response.get("status", "unknown").lower()

            # Map API status to our OrderStatus enum
            # CoW Protocol API statuses: open, fulfilled, cancelled, expired
            status_map = {
                "open": OrderStatus.OPEN,
                "fulfilled": OrderStatus.FILLED,
                "cancelled": OrderStatus.CANCELLED,
                "expired": OrderStatus.EXPIRED,
            }

            new_status = status_map.get(api_status, OrderStatus.OPEN)

            # Extract filled amount if available
            filled_amount = None
            if "executedSellAmount" in order_response:
                executed_sell = str(order_response["executedSellAmount"])
                if int(executed_sell) > 0:
                    filled_amount = executed_sell

            # Always update the status (not just when executedSellAmount > 0)
            self.update_order_status(order_uid, new_status, filled_amount=filled_amount)

            # Log status changes for debugging
            if new_status == OrderStatus.FILLED and filled_amount:
                print(f"  ✓ Order {order_uid[:20]}... filled with amount {filled_amount}")

            return new_status

        except Exception as e:
            # If API call fails (e.g., 404 for unknown order), keep current status
            # This can happen for very new orders that haven't been indexed yet
            print(f"  Warning: Failed to poll order {order_uid[:20]}...: {type(e).__name__}: {e}")
            return metadata.current_status

    async def monitor_order(
        self,
        order_uid: str,
        api_client: Any | None = None,
    ) -> OrderMetadata:
        """
        Monitor an order until it reaches a terminal state.

        Polls the order status at regular intervals and updates metadata
        until the order is filled, expired, cancelled, or failed.

        Args:
            order_uid: The order UID to monitor
            api_client: Optional API client for polling (mock if None)

        Returns:
            The final OrderMetadata
        """
        attempts = 0

        while attempts < self.max_poll_attempts:
            metadata = self.get_order(order_uid)
            if metadata is None:
                break

            if metadata.is_terminal_state():
                break

            # Poll status (mock implementation)
            if api_client is not None:
                status = await self.poll_order_status(order_uid, api_client)
                self.update_order_status(order_uid, status)

            await asyncio.sleep(self.poll_interval)
            attempts += 1

        # If we hit max attempts, stop monitoring but don't mark as failed
        # The orchestrator's settlement wait period will continue monitoring
        # and will determine the final status
        metadata = self.get_order(order_uid)

        return metadata or OrderMetadata(
            order_uid=order_uid,
            owner="",
            creation_time=time.time(),
        )

    def start_monitoring(self, order_uid: str, api_client: Any | None = None) -> asyncio.Task:
        """
        Start monitoring an order in the background.

        Args:
            order_uid: The order UID to monitor
            api_client: Optional API client for polling

        Returns:
            The asyncio Task for monitoring
        """
        task = asyncio.create_task(self.monitor_order(order_uid, api_client))
        self._polling_tasks[order_uid] = task
        return task

    async def stop_monitoring(self, order_uid: str) -> None:
        """
        Stop monitoring an order.

        Args:
            order_uid: The order UID to stop monitoring
        """
        if order_uid in self._polling_tasks:
            task = self._polling_tasks[order_uid]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self._polling_tasks[order_uid]

    async def stop_all_monitoring(self) -> None:
        """Stop monitoring all orders."""
        for order_uid in list(self._polling_tasks.keys()):
            await self.stop_monitoring(order_uid)

    def get_metrics(self) -> OrderMetrics:
        """
        Calculate aggregated metrics for all tracked orders.

        Returns:
            OrderMetrics with summary statistics
        """
        orders = self.get_all_orders()
        metrics = OrderMetrics(total_orders=len(orders))

        if not orders:
            return metrics

        # Count orders by status
        for order in orders:
            status = order.current_status
            if status == OrderStatus.CREATED:
                metrics.orders_created += 1
            elif status == OrderStatus.SUBMITTED:
                metrics.orders_submitted += 1
            elif status in (OrderStatus.ACCEPTED, OrderStatus.OPEN):
                metrics.orders_accepted += 1
            elif status == OrderStatus.FILLED:
                metrics.orders_filled += 1
            elif status == OrderStatus.PARTIALLY_FILLED:
                metrics.orders_partially_filled += 1
            elif status == OrderStatus.EXPIRED:
                metrics.orders_expired += 1
            elif status == OrderStatus.CANCELLED:
                metrics.orders_cancelled += 1
            elif status == OrderStatus.FAILED:
                metrics.orders_failed += 1

        # Calculate average times
        times_to_submit = [t for order in orders if (t := order.get_time_to_submit()) is not None]
        times_to_accept = [t for order in orders if (t := order.get_time_to_accept()) is not None]
        times_to_fill = [t for order in orders if (t := order.get_time_to_fill()) is not None]
        total_lifecycle_times = [
            t for order in orders if (t := order.get_total_lifecycle_time()) is not None
        ]

        if times_to_submit:
            metrics.avg_time_to_submit = sum(times_to_submit) / len(times_to_submit)
        if times_to_accept:
            metrics.avg_time_to_accept = sum(times_to_accept) / len(times_to_accept)
        if times_to_fill:
            metrics.avg_time_to_fill = sum(times_to_fill) / len(times_to_fill)
        if total_lifecycle_times:
            metrics.avg_total_lifecycle_time = sum(total_lifecycle_times) / len(
                total_lifecycle_times
            )

        return metrics
