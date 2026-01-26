"""
Orchestration for managing multiple concurrent trader simulations.

This module provides coordination of multiple trader simulators with graceful
startup/shutdown, error handling, and performance monitoring.
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any

from .conditional_order_factory import ConditionalOrderFactory
from .order_factory import OrderFactory
from .order_signer import ConditionalOrderSigner, OrderSigner
from .order_tracker import OrderTracker
from .trader_account import TraderPool
from .trader_simulator import TraderBehaviorConfig, TraderSimulator


@dataclass
class OrchestrationConfig:
    """
    Configuration for trader orchestration.

    Controls the number of concurrent traders, timing, and error handling behavior.
    """

    num_traders: int = 10
    duration: float = 60.0  # Simulation duration in seconds
    startup_interval: float = 0.5  # Seconds between starting each trader
    restart_on_failure: bool = True  # Restart traders on failure
    max_restarts_per_trader: int = 3  # Maximum restart attempts
    graceful_shutdown_timeout: float = 10.0  # Timeout for graceful shutdown


class TraderOrchestrator:
    """
    Orchestrates multiple concurrent trader simulations.

    Manages trader lifecycle, handles failures, and provides coordinated
    startup and shutdown for load testing scenarios.
    """

    def __init__(
        self,
        trader_pool: TraderPool,
        order_factory: OrderFactory,
        conditional_order_factory: ConditionalOrderFactory,
        order_signer: OrderSigner,
        conditional_order_signer: ConditionalOrderSigner,
        order_tracker: OrderTracker,
        default_behavior_config: TraderBehaviorConfig,
        orchestration_config: OrchestrationConfig,
        api_client: Any | None = None,
    ):
        """
        Initialize the trader orchestrator.

        Args:
            trader_pool: Pool of trader accounts
            order_factory: Factory for standard orders
            conditional_order_factory: Factory for conditional orders
            order_signer: Signer for standard orders
            conditional_order_signer: Signer for conditional orders
            order_tracker: Shared order tracker for all traders
            default_behavior_config: Default behavior configuration for traders
            orchestration_config: Configuration for orchestration
            api_client: Optional API client for order submission
        """
        self.trader_pool = trader_pool
        self.order_factory = order_factory
        self.conditional_order_factory = conditional_order_factory
        self.order_signer = order_signer
        self.conditional_order_signer = conditional_order_signer
        self.order_tracker = order_tracker
        self.default_behavior_config = default_behavior_config
        self.orchestration_config = orchestration_config
        self.api_client = api_client

        self.simulators: list[TraderSimulator] = []
        self.tasks: list[asyncio.Task] = []
        self.restart_counts: dict[int, int] = {}
        self._running = False
        self._start_time: float = 0.0

    def _create_simulator(self, trader_index: int) -> TraderSimulator:
        """
        Create a trader simulator for the given trader index.

        Args:
            trader_index: Index of trader in the pool

        Returns:
            A configured TraderSimulator instance
        """
        trader = self.trader_pool.get_trader(trader_index)

        # Could customize behavior per trader here
        behavior_config = self.default_behavior_config

        return TraderSimulator(
            trader=trader,
            order_factory=self.order_factory,
            conditional_order_factory=self.conditional_order_factory,
            order_signer=self.order_signer,
            conditional_order_signer=self.conditional_order_signer,
            order_tracker=self.order_tracker,
            behavior_config=behavior_config,
            api_client=self.api_client,
        )

    async def _run_trader_with_restart(
        self,
        trader_index: int,
        duration: float,
    ) -> None:
        """
        Run a trader with automatic restart on failure.

        Args:
            trader_index: Index of the trader to run
            duration: Duration to run the trader
        """
        self.restart_counts[trader_index] = 0

        while self._running:
            # Check if we've exceeded max restarts
            if (
                self.orchestration_config.restart_on_failure
                and self.restart_counts[trader_index]
                >= self.orchestration_config.max_restarts_per_trader
            ):
                print(
                    f"Trader {trader_index} exceeded max restarts "
                    f"({self.orchestration_config.max_restarts_per_trader}), stopping"
                )
                break

            # Calculate remaining duration
            elapsed = time.time() - self._start_time
            remaining = duration - elapsed
            if remaining <= 0:
                break

            try:
                # Create and run simulator
                simulator = self._create_simulator(trader_index)
                await simulator.run(remaining)

                # If we complete successfully, we're done
                break

            except Exception as e:
                print(f"Trader {trader_index} failed with error: {e}")

                if not self.orchestration_config.restart_on_failure:
                    break

                # Increment restart count and retry
                self.restart_counts[trader_index] += 1
                print(
                    f"Restarting trader {trader_index} "
                    f"(attempt {self.restart_counts[trader_index]})"
                )

                # Small delay before restart
                await asyncio.sleep(1.0)

    async def run(self) -> None:
        """
        Run the orchestrated trader simulation.

        Starts all traders with staggered timing and runs for the configured duration.
        """
        self._running = True
        self._start_time = time.time()

        config = self.orchestration_config
        num_traders = min(config.num_traders, self.trader_pool.get_pool_size())

        print(f"Starting {num_traders} traders...")

        try:
            # Start traders with staggered timing
            for i in range(num_traders):
                if not self._running:
                    break

                task = asyncio.create_task(
                    self._run_trader_with_restart(i, config.duration)
                )
                self.tasks.append(task)

                # Stagger startup
                if i < num_traders - 1:
                    await asyncio.sleep(config.startup_interval)

            print(f"All {len(self.tasks)} traders started")

            # Wait for all traders to complete
            await asyncio.gather(*self.tasks, return_exceptions=True)

        finally:
            self._running = False
            print("All traders completed")

    async def start(self) -> asyncio.Task:
        """
        Start orchestration in background.

        Returns:
            The asyncio Task for the orchestration
        """
        return asyncio.create_task(self.run())

    async def stop(self) -> None:
        """
        Stop all traders gracefully.

        Attempts to stop all traders within the configured timeout,
        then cancels any remaining tasks.
        """
        print("Stopping all traders...")
        self._running = False

        # Stop all simulators
        for simulator in self.simulators:
            try:
                await asyncio.wait_for(
                    simulator.stop(),
                    timeout=self.orchestration_config.graceful_shutdown_timeout,
                )
            except asyncio.TimeoutError:
                print(f"Timeout stopping simulator, forcing cancellation")

        # Cancel all tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()

        # Wait for cancellations to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)

        # Stop order tracking
        await self.order_tracker.stop_all_monitoring()

        print("All traders stopped")

    def get_status(self) -> dict[str, Any]:
        """
        Get current orchestration status.

        Returns:
            Dictionary with status information
        """
        elapsed = time.time() - self._start_time if self._start_time > 0 else 0

        return {
            "running": self._running,
            "num_traders": len(self.tasks),
            "elapsed_time": elapsed,
            "total_orders_submitted": self.trader_pool.get_total_orders_submitted(),
            "restart_counts": self.restart_counts.copy(),
            "order_metrics": self.order_tracker.get_metrics(),
        }

    def get_metrics(self) -> dict[str, Any]:
        """
        Get comprehensive metrics from the simulation.

        Returns:
            Dictionary with detailed metrics
        """
        status = self.get_status()
        order_metrics = self.order_tracker.get_metrics()

        return {
            "orchestration": {
                "num_traders": len(self.tasks),
                "elapsed_time": status["elapsed_time"],
                "total_restarts": sum(self.restart_counts.values()),
            },
            "orders": {
                "total_submitted": self.trader_pool.get_total_orders_submitted(),
                "total_tracked": order_metrics.total_orders,
                "orders_filled": order_metrics.orders_filled,
                "orders_failed": order_metrics.orders_failed,
                "orders_expired": order_metrics.orders_expired,
            },
            "performance": {
                "orders_per_second": (
                    self.trader_pool.get_total_orders_submitted() / status["elapsed_time"]
                    if status["elapsed_time"] > 0
                    else 0.0
                ),
                "avg_time_to_submit": order_metrics.avg_time_to_submit,
                "avg_time_to_accept": order_metrics.avg_time_to_accept,
                "avg_time_to_fill": order_metrics.avg_time_to_fill,
                "avg_total_lifecycle_time": order_metrics.avg_total_lifecycle_time,
            },
        }


async def run_load_test(
    num_traders: int = 10,
    duration: float = 60.0,
    trader_pool: TraderPool | None = None,
    order_factory: OrderFactory | None = None,
    conditional_order_factory: ConditionalOrderFactory | None = None,
    order_signer: OrderSigner | None = None,
    conditional_order_signer: ConditionalOrderSigner | None = None,
    order_tracker: OrderTracker | None = None,
    behavior_config: TraderBehaviorConfig | None = None,
    orchestration_config: OrchestrationConfig | None = None,
    api_client: Any | None = None,
) -> dict[str, Any]:
    """
    Convenience function to run a complete load test.

    This function sets up and runs a load test with the specified parameters,
    providing a simple interface for common testing scenarios.

    Args:
        num_traders: Number of concurrent traders
        duration: Test duration in seconds
        trader_pool: Optional trader pool (creates default if None)
        order_factory: Optional order factory (creates default if None)
        conditional_order_factory: Optional conditional order factory (creates default if None)
        order_signer: Optional order signer (creates default if None)
        conditional_order_signer: Optional conditional order signer (creates default if None)
        order_tracker: Optional order tracker (creates default if None)
        behavior_config: Optional behavior config (uses default if None)
        orchestration_config: Optional orchestration config (uses default if None)
        api_client: Optional API client for order submission

    Returns:
        Dictionary with test results and metrics
    """
    # Create default components if not provided
    if trader_pool is None:
        trader_pool = TraderPool(num_traders=num_traders)

    if order_tracker is None:
        order_tracker = OrderTracker()

    if behavior_config is None:
        behavior_config = TraderBehaviorConfig()

    if orchestration_config is None:
        orchestration_config = OrchestrationConfig(
            num_traders=num_traders,
            duration=duration,
        )

    # Note: order_factory, conditional_order_factory, order_signer, and
    # conditional_order_signer would need to be created with proper
    # configuration (chain_id, contract addresses, etc.)
    # For now, we require them to be passed in or this function will fail

    if order_factory is None or order_signer is None:
        raise ValueError(
            "order_factory and order_signer must be provided"
        )

    if conditional_order_factory is None or conditional_order_signer is None:
        raise ValueError(
            "conditional_order_factory and conditional_order_signer must be provided"
        )

    # Create orchestrator
    orchestrator = TraderOrchestrator(
        trader_pool=trader_pool,
        order_factory=order_factory,
        conditional_order_factory=conditional_order_factory,
        order_signer=order_signer,
        conditional_order_signer=conditional_order_signer,
        order_tracker=order_tracker,
        default_behavior_config=behavior_config,
        orchestration_config=orchestration_config,
        api_client=api_client,
    )

    # Run the test
    await orchestrator.run()

    # Return metrics
    return orchestrator.get_metrics()
