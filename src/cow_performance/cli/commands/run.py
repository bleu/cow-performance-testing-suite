"""Run command implementation for performance testing."""

import asyncio
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from cow_performance.load_generation import (
    ConditionalOrderFactory,
    OrchestrationConfig,
    OrderFactory,
    OrderSigner,
    OrderTracker,
    TraderBehaviorConfig,
    TraderOrchestrator,
    TraderPool,
    TradingPattern,
    create_mainnet_token_registry,
)
from cow_performance.load_generation.order_signer import ConditionalOrderSigner

from ..config import PerformanceTestConfig
from ..output import (
    create_result_filename,
    format_metrics_json,
    format_metrics_table,
    save_metrics_to_file,
)


class GracefulShutdownHandler:
    """Handles graceful shutdown on SIGINT (Ctrl+C)."""

    def __init__(self, orchestrator: TraderOrchestrator):
        """Initialize the shutdown handler.

        Args:
            orchestrator: The TraderOrchestrator to stop on signal
        """
        self.orchestrator = orchestrator
        self.shutdown_requested = False

    def handle_signal(self, signum: int, frame: Any) -> None:
        """Handle shutdown signal.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        if not self.shutdown_requested:
            self.shutdown_requested = True
            print("\n\nShutdown requested, stopping traders gracefully...")
            # The orchestrator's run() method will check _running flag
            self.orchestrator._running = False


async def run_performance_test(
    config: PerformanceTestConfig,
    traders: int | None = None,
    duration: int | None = None,
    verbose: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Run a performance test with the given configuration.

    Args:
        config: Performance test configuration
        traders: Optional override for number of traders
        duration: Optional override for test duration (seconds)
        verbose: Enable verbose output
        dry_run: Perform dry run without submitting orders

    Returns:
        Dictionary with test results and metrics

    Raises:
        ValueError: If configuration is invalid
    """
    console = Console()

    # Use overrides or config defaults
    num_traders = traders if traders is not None else config.default_trader_count
    test_duration = duration if duration is not None else config.default_duration

    if verbose:
        console.print("[bold cyan]Configuration:[/bold cyan]")
        console.print(f"  Traders: {num_traders}")
        console.print(f"  Duration: {test_duration}s")
        console.print(f"  Chain ID: {config.network.chain_id}")
        console.print(f"  API URL: {config.api.base_url}")
        console.print()

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No orders will be submitted[/yellow]")
        console.print()

    # Create token registry
    token_registry = create_mainnet_token_registry()

    # Create trader pool
    trader_pool = TraderPool(num_traders=num_traders)

    # Create order factories
    order_factory = OrderFactory(
        token_pair_registry=token_registry,
        chain_id=config.network.chain_id,
        settlement_contract=config.network.settlement_contract,
        valid_duration=3600,  # 1 hour validity
    )

    # Use a dummy Safe address for conditional orders (will be replaced with actual Safe per trader)
    dummy_safe_address = "0x0000000000000000000000000000000000000001"
    conditional_order_factory = ConditionalOrderFactory(
        token_pair_registry=token_registry,
        chain_id=config.network.chain_id,
        safe_wallet_address=dummy_safe_address,
    )

    # Create order signers
    order_signer = OrderSigner(
        chain_id=config.network.chain_id,
        settlement_contract=config.network.settlement_contract,
    )

    conditional_order_signer = ConditionalOrderSigner(
        chain_id=config.network.chain_id,
        composable_cow_contract=config.network.composable_cow_contract,
    )

    # Create order tracker
    order_tracker = OrderTracker(
        poll_interval=5.0,  # Poll every 5 seconds
        max_poll_attempts=12,  # Up to 60 seconds
    )

    # Create trader behavior config from app config
    behavior_config = TraderBehaviorConfig(
        pattern=TradingPattern.CONSTANT_RATE,
        base_rate=60.0,  # 60 orders per minute (1 per second)
        market_order_ratio=config.market_order_ratio,
        limit_order_ratio=config.limit_order_ratio,
        twap_order_ratio=config.twap_order_ratio,
        stop_loss_order_ratio=config.stop_loss_order_ratio,
        good_after_time_order_ratio=config.good_after_time_order_ratio,
    )

    # Create orchestration config
    orchestration_config = OrchestrationConfig(
        num_traders=num_traders,
        duration=float(test_duration),
        startup_interval=config.default_startup_interval,
        restart_on_failure=True,
        max_restarts_per_trader=3,
        graceful_shutdown_timeout=10.0,
    )

    # Create orchestrator (no API client in dry run mode)
    api_client = None if dry_run else None  # TODO: Create API client when needed

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

    # Set up graceful shutdown handler
    shutdown_handler = GracefulShutdownHandler(orchestrator)
    signal.signal(signal.SIGINT, shutdown_handler.handle_signal)

    # Run the test with progress display
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(
            f"Running performance test with {num_traders} traders...",
            total=None,
        )

        try:
            # Start test
            start_time = datetime.now()
            await orchestrator.run()
            end_time = datetime.now()

            progress.update(task, description="[bold green]Test completed!")

        except Exception as e:
            progress.update(task, description="[bold red]Test failed!")
            console.print(f"\n[bold red]Error:[/bold red] {e}")
            raise

    # Get metrics
    metrics = orchestrator.get_metrics()

    # Add timing information
    metrics["timing"] = {
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_seconds": (end_time - start_time).total_seconds(),
    }

    # Add configuration info
    metrics["config"] = {
        "num_traders": num_traders,
        "duration": test_duration,
        "chain_id": config.network.chain_id,
        "api_url": config.api.base_url,
        "dry_run": dry_run,
    }

    # Update orchestration metrics with actual config values
    metrics["orchestration"]["num_traders"] = num_traders
    metrics["orchestration"]["duration"] = test_duration
    metrics["orchestration"]["startup_interval"] = config.default_startup_interval

    # Add order type breakdown from trader pool
    total_orders = trader_pool.get_total_orders_submitted()
    metrics["orders"]["total_submitted"] = total_orders
    metrics["orders"]["market_orders"] = int(total_orders * config.market_order_ratio)
    metrics["orders"]["limit_orders"] = int(total_orders * config.limit_order_ratio)
    metrics["orders"]["twap_orders"] = int(total_orders * config.twap_order_ratio)
    metrics["orders"]["stop_loss_orders"] = int(total_orders * config.stop_loss_order_ratio)
    metrics["orders"]["good_after_time_orders"] = int(
        total_orders * config.good_after_time_order_ratio
    )

    # Add trader statistics
    active_traders = sum(
        1 for trader in trader_pool.get_all_traders() if trader.orders_submitted > 0
    )
    metrics["traders"] = {
        "active_traders": active_traders,
        "total_traders": num_traders,
    }

    # Add performance metrics
    elapsed = metrics["orchestration"]["elapsed_time"]
    metrics["performance"]["orders_per_second"] = total_orders / elapsed if elapsed > 0 else 0.0
    metrics["performance"]["avg_order_latency_ms"] = (
        (elapsed * 1000 / total_orders) if total_orders > 0 else 0.0
    )

    return metrics


def run_command(
    config: PerformanceTestConfig,
    traders: int | None = None,
    duration: int | None = None,
    output_format: str | None = None,
    save_results: bool = False,
    output_file: str | None = None,
    verbose: bool = False,
    dry_run: bool = False,
) -> None:
    """Run command entry point.

    Args:
        config: Performance test configuration
        traders: Optional override for number of traders
        duration: Optional override for test duration (seconds)
        output_format: Optional override for output format
        save_results: Whether to save results to file
        output_file: Optional path to save results
        verbose: Enable verbose output
        dry_run: Perform dry run without submitting orders

    Raises:
        SystemExit: On error (with appropriate exit code)
    """
    console = Console()

    try:
        # Run the test
        metrics = asyncio.run(
            run_performance_test(
                config=config,
                traders=traders,
                duration=duration,
                verbose=verbose,
                dry_run=dry_run,
            )
        )

        # Determine output format
        fmt = output_format or config.output.format

        # Display results
        console.print("\n[bold green]Test Results:[/bold green]\n")

        if fmt == "json":
            console.print(format_metrics_json(metrics))
        elif fmt == "table":
            format_metrics_table(metrics, console)
        elif fmt in ["csv", "prometheus"]:
            # For non-interactive formats, show as JSON on console
            # but save in requested format if saving
            format_metrics_table(metrics, console)
        else:
            console.print(f"[bold red]Error:[/bold red] Unknown output format: {fmt}")
            sys.exit(1)

        # Save results if requested
        should_save = save_results or config.output.save_results or output_file
        if should_save:
            if output_file:
                output_path = Path(output_file)
            else:
                # Auto-generate filename
                results_dir = config.output.results_dir
                results_dir.mkdir(parents=True, exist_ok=True)
                filename = create_result_filename(
                    prefix="perf-test",
                    output_format=fmt,
                )
                output_path = results_dir / filename

            save_metrics_to_file(metrics, fmt, output_path)
            console.print(f"\n[bold green]✓[/bold green] Results saved to: {output_path}")

    except KeyboardInterrupt:
        console.print("\n[yellow]Test interrupted by user[/yellow]")
        sys.exit(130)  # Standard exit code for SIGINT
    except ValueError as e:
        console.print(f"[bold red]Configuration Error:[/bold red] {e}")
        sys.exit(3)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)
