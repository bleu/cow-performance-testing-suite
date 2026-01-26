"""
Trader simulation for realistic user behavior patterns.

This module provides trader simulation with configurable behavior patterns,
supporting all order types (market, limit, TWAP, stop-loss, good-after-time).
"""

import asyncio
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .conditional_order_factory import ConditionalOrderFactory
from .order_factory import OrderFactory
from .order_signer import ConditionalOrderSigner, OrderSigner
from .order_tracker import OrderStatus, OrderTracker
from .trader_account import TraderAccount


class TradingPattern(str, Enum):
    """Trading behavior patterns for simulation."""

    CONSTANT_RATE = "constant_rate"  # Fixed interval between orders
    RANDOM_INTERVAL = "random_interval"  # Random intervals within a range
    BURST = "burst"  # Bursts of activity followed by quiet periods
    TIME_BASED = "time_based"  # More active during certain periods


@dataclass
class TraderBehaviorConfig:
    """
    Configuration for trader behavior simulation.

    Controls trading patterns, order preferences, and timing parameters.
    """

    pattern: TradingPattern = TradingPattern.CONSTANT_RATE

    # Order submission rate (orders per minute)
    base_rate: float = 6.0

    # Order type distribution (sum should be 1.0)
    market_order_ratio: float = 0.4
    limit_order_ratio: float = 0.4
    twap_order_ratio: float = 0.1
    stop_loss_order_ratio: float = 0.05
    good_after_time_order_ratio: float = 0.05

    # Random interval pattern parameters (seconds)
    min_interval: float = 5.0
    max_interval: float = 30.0

    # Burst pattern parameters
    burst_size: int = 5  # Orders per burst
    burst_interval: float = 2.0  # Seconds between orders in burst
    quiet_period: float = 60.0  # Seconds between bursts

    # Time-based pattern parameters
    active_hours: list[int] | None = None  # Hours when more active (0-23)
    active_multiplier: float = 2.0  # Rate multiplier during active hours

    # Order size preferences (multipliers for template amounts)
    min_size_multiplier: float = 0.5
    max_size_multiplier: float = 2.0

    # Think time (delay between decision and action, seconds)
    min_think_time: float = 0.5
    max_think_time: float = 2.0

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        total_ratio = (
            self.market_order_ratio
            + self.limit_order_ratio
            + self.twap_order_ratio
            + self.stop_loss_order_ratio
            + self.good_after_time_order_ratio
        )
        if not 0.99 <= total_ratio <= 1.01:  # Allow small floating point errors
            raise ValueError(f"Order type ratios must sum to 1.0, got {total_ratio}")

        if self.base_rate <= 0:
            raise ValueError("base_rate must be positive")


class TraderSimulator:
    """
    Simulates individual trader behavior with configurable patterns.

    Generates and submits orders of all types (market, limit, TWAP, stop-loss,
    good-after-time) according to configured behavior patterns.
    """

    def __init__(
        self,
        trader: TraderAccount,
        order_factory: OrderFactory,
        conditional_order_factory: ConditionalOrderFactory,
        order_signer: OrderSigner,
        conditional_order_signer: ConditionalOrderSigner,
        order_tracker: OrderTracker,
        behavior_config: TraderBehaviorConfig,
        api_client: Any | None = None,
    ):
        """
        Initialize trader simulator.

        Args:
            trader: The trader account to simulate
            order_factory: Factory for generating standard orders
            conditional_order_factory: Factory for generating conditional orders
            order_signer: Signer for standard orders
            conditional_order_signer: Signer for conditional orders
            order_tracker: Tracker for monitoring order lifecycle
            behavior_config: Configuration for trading behavior
            api_client: Optional API client for order submission
        """
        self.trader = trader
        self.order_factory = order_factory
        self.conditional_order_factory = conditional_order_factory
        self.order_signer = order_signer
        self.conditional_order_signer = conditional_order_signer
        self.order_tracker = order_tracker
        self.behavior_config = behavior_config
        self.api_client = api_client

        self._running = False
        self._task: asyncio.Task | None = None

    def _get_order_interval(self) -> float:
        """
        Calculate the next order interval based on behavior pattern.

        Returns:
            Seconds until next order
        """
        config = self.behavior_config
        base_interval = 60.0 / config.base_rate  # Convert rate to interval

        if config.pattern == TradingPattern.CONSTANT_RATE:
            return base_interval

        elif config.pattern == TradingPattern.RANDOM_INTERVAL:
            return random.uniform(config.min_interval, config.max_interval)

        elif config.pattern == TradingPattern.BURST:
            # Handled separately in _burst_pattern_loop
            return base_interval

        elif config.pattern == TradingPattern.TIME_BASED:
            current_hour = time.localtime().tm_hour
            if config.active_hours and current_hour in config.active_hours:
                return base_interval / config.active_multiplier
            return base_interval

        return base_interval

    def _select_order_type(self) -> str:
        """
        Select order type based on configured distribution.

        Returns:
            Order type: 'market', 'limit', 'twap', 'stop_loss', 'good_after_time'
        """
        config = self.behavior_config
        rand = random.random()

        cumulative = 0.0
        for order_type, ratio in [
            ("market", config.market_order_ratio),
            ("limit", config.limit_order_ratio),
            ("twap", config.twap_order_ratio),
            ("stop_loss", config.stop_loss_order_ratio),
            ("good_after_time", config.good_after_time_order_ratio),
        ]:
            cumulative += ratio
            if rand <= cumulative:
                return order_type

        return "market"  # Fallback

    async def _apply_think_time(self) -> None:
        """Apply random think time before action."""
        think_time = random.uniform(
            self.behavior_config.min_think_time,
            self.behavior_config.max_think_time,
        )
        await asyncio.sleep(think_time)

    async def _generate_and_submit_order(self) -> None:
        """Generate and submit a single order based on behavior configuration."""
        order_type = self._select_order_type()

        # Apply think time
        await self._apply_think_time()

        try:
            if order_type in ("market", "limit"):
                await self._submit_standard_order(order_type)
            elif order_type == "twap":
                await self._submit_twap_order()
            elif order_type == "stop_loss":
                await self._submit_stop_loss_order()
            elif order_type == "good_after_time":
                await self._submit_good_after_time_order()
        except Exception as e:
            # Log error but continue trading
            print(f"Error submitting {order_type} order: {e}")

    async def _submit_standard_order(self, order_type: str) -> None:
        """
        Generate and submit a standard order (market or limit).

        Args:
            order_type: Either 'market' or 'limit'
        """
        # Generate order using factory (already signed)
        if order_type == "market":
            signed_order = self.order_factory.create_market_order(
                trader_account=self.trader.get_account()
            )
        else:
            signed_order = self.order_factory.create_limit_order(
                trader_account=self.trader.get_account()
            )

        # Track order creation
        # Note: In real implementation, order_uid would come from API response
        order_uid = f"0x{'0' * 56}{int(time.time())}"  # Mock UID
        self.order_tracker.track_order(
            order_uid=order_uid,
            owner=self.trader.address,
            sell_token=signed_order.sellToken,
            buy_token=signed_order.buyToken,
            sell_amount=signed_order.sellAmount,
            buy_amount=signed_order.buyAmount,
        )

        # Update status to submitted
        self.order_tracker.update_order_status(order_uid, OrderStatus.SUBMITTED)

        # Submit to API
        if self.api_client is not None:
            try:
                # Submit order to orderbook API
                await self.api_client.submit_order(signed_order.model_dump(by_alias=True))
                self.order_tracker.update_order_status(order_uid, OrderStatus.ACCEPTED)
            except Exception as e:
                # Mark as failed if submission fails
                self.order_tracker.update_order_status(order_uid, OrderStatus.FAILED)
                # Re-raise to let orchestrator handle it
                raise RuntimeError(f"Failed to submit order: {e}") from e
        else:
            # Mock acceptance in dry-run mode
            self.order_tracker.update_order_status(order_uid, OrderStatus.ACCEPTED)

        # Increment trader stats
        self.trader.increment_orders_submitted()

        # Start monitoring in background
        self.order_tracker.start_monitoring(order_uid, self.api_client)

    async def _submit_twap_order(self) -> None:
        """Generate and submit a TWAP order."""
        # Generate TWAP order (returns ConditionalOrder with embedded TWAP params)
        self.conditional_order_factory.create_twap_order()

        # Track order (mock - in reality would track after submission)
        order_uid = f"0x{'0' * 56}{int(time.time())}"  # Mock UID
        # Note: For TWAP, we track the total amounts
        self.order_tracker.track_order(
            order_uid=order_uid,
            owner=self.trader.address,
            sell_token="0x0000000000000000000000000000000000000000",  # Placeholder
            buy_token="0x0000000000000000000000000000000000000000",  # Placeholder
            sell_amount="0",  # Placeholder
            buy_amount="0",  # Placeholder
        )

        # Update status
        self.order_tracker.update_order_status(order_uid, OrderStatus.SUBMITTED)

        # Submit (mock)
        if self.api_client is None:
            self.order_tracker.update_order_status(order_uid, OrderStatus.ACCEPTED)

        self.trader.increment_orders_submitted()
        self.order_tracker.start_monitoring(order_uid, self.api_client)

    async def _submit_stop_loss_order(self) -> None:
        """Generate and submit a stop-loss order."""
        # Generate stop-loss order (returns ConditionalOrder with embedded params)
        self.conditional_order_factory.create_stop_loss_order()

        # Track order (mock - in reality would track after submission)
        order_uid = f"0x{'0' * 56}{int(time.time())}"  # Mock UID
        self.order_tracker.track_order(
            order_uid=order_uid,
            owner=self.trader.address,
            sell_token="0x0000000000000000000000000000000000000000",  # Placeholder
            buy_token="0x0000000000000000000000000000000000000000",  # Placeholder
            sell_amount="0",  # Placeholder
            buy_amount="0",  # Placeholder
        )

        # Update status
        self.order_tracker.update_order_status(order_uid, OrderStatus.SUBMITTED)

        # Submit (mock)
        if self.api_client is None:
            self.order_tracker.update_order_status(order_uid, OrderStatus.ACCEPTED)

        self.trader.increment_orders_submitted()
        self.order_tracker.start_monitoring(order_uid, self.api_client)

    async def _submit_good_after_time_order(self) -> None:
        """Generate and submit a good-after-time order."""
        # Generate good-after-time order (returns ConditionalOrder with embedded params)
        self.conditional_order_factory.create_good_after_time_order()

        # Track order (mock - in reality would track after submission)
        order_uid = f"0x{'0' * 56}{int(time.time())}"  # Mock UID
        self.order_tracker.track_order(
            order_uid=order_uid,
            owner=self.trader.address,
            sell_token="0x0000000000000000000000000000000000000000",  # Placeholder
            buy_token="0x0000000000000000000000000000000000000000",  # Placeholder
            sell_amount="0",  # Placeholder
            buy_amount="0",  # Placeholder
        )

        # Update status
        self.order_tracker.update_order_status(order_uid, OrderStatus.SUBMITTED)

        # Submit (mock)
        if self.api_client is None:
            self.order_tracker.update_order_status(order_uid, OrderStatus.ACCEPTED)

        self.trader.increment_orders_submitted()
        self.order_tracker.start_monitoring(order_uid, self.api_client)

    async def _constant_rate_loop(self, duration: float) -> None:
        """Run trading loop with constant rate pattern."""
        end_time = time.time() + duration

        while self._running and time.time() < end_time:
            await self._generate_and_submit_order()
            interval = self._get_order_interval()
            await asyncio.sleep(interval)

    async def _random_interval_loop(self, duration: float) -> None:
        """Run trading loop with random interval pattern."""
        # Same as constant rate, but _get_order_interval returns random values
        await self._constant_rate_loop(duration)

    async def _burst_pattern_loop(self, duration: float) -> None:
        """Run trading loop with burst pattern."""
        end_time = time.time() + duration
        config = self.behavior_config

        while self._running and time.time() < end_time:
            # Generate burst
            for _ in range(config.burst_size):
                if not self._running or time.time() >= end_time:
                    break
                await self._generate_and_submit_order()
                await asyncio.sleep(config.burst_interval)

            # Quiet period
            await asyncio.sleep(config.quiet_period)

    async def _time_based_loop(self, duration: float) -> None:
        """Run trading loop with time-based pattern."""
        # Same as constant rate, but _get_order_interval adjusts based on time
        await self._constant_rate_loop(duration)

    async def run(self, duration: float) -> None:
        """
        Run trader simulation for specified duration.

        Args:
            duration: Duration to run simulation in seconds
        """
        self._running = True

        try:
            if self.behavior_config.pattern == TradingPattern.CONSTANT_RATE:
                await self._constant_rate_loop(duration)
            elif self.behavior_config.pattern == TradingPattern.RANDOM_INTERVAL:
                await self._random_interval_loop(duration)
            elif self.behavior_config.pattern == TradingPattern.BURST:
                await self._burst_pattern_loop(duration)
            elif self.behavior_config.pattern == TradingPattern.TIME_BASED:
                await self._time_based_loop(duration)
        finally:
            self._running = False

    def start(self, duration: float) -> asyncio.Task:
        """
        Start trader simulation in background.

        Args:
            duration: Duration to run simulation in seconds

        Returns:
            The asyncio Task for the simulation
        """
        self._task = asyncio.create_task(self.run(duration))
        return self._task

    async def stop(self) -> None:
        """Stop the trader simulation gracefully."""
        self._running = False
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except TimeoutError:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass

    def is_running(self) -> bool:
        """
        Check if trader is currently running.

        Returns:
            True if running, False otherwise
        """
        return self._running
