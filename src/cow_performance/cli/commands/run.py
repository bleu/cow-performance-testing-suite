"""Run command implementation for performance testing."""

import asyncio
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from web3 import Web3

from cow_performance.api import OrderbookClient
from cow_performance.load_generation import (
    ConditionalOrderFactory,
    OrchestrationConfig,
    OrderFactory,
    OrderSigner,
    OrderTracker,
    TraderBehaviorConfig,
    TraderOrchestrator,
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
from ..wallet_funding import create_trader_pool_from_config, fund_trader_pool


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
    settlement_wait: int | None = None,
    verbose: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Run a performance test with the given configuration.

    Args:
        config: Performance test configuration
        traders: Optional override for number of traders
        duration: Optional override for test duration (seconds)
        settlement_wait: Optional override for settlement wait time (seconds, default 300)
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
    settlement_wait_time = settlement_wait if settlement_wait is not None else 300.0  # Default 5 minutes

    if verbose:
        console.print("[bold cyan]Configuration:[/bold cyan]")
        console.print(f"  Traders: {num_traders}")
        console.print(f"  Duration: {test_duration}s")
        console.print(f"  Settlement wait: {settlement_wait_time}s")
        console.print(f"  Chain ID: {config.network.chain_id}")
        console.print(f"  API URL: {config.api.base_url}")
        console.print()

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No orders will be submitted[/yellow]")
        console.print()

    # Create token registry
    token_registry = create_mainnet_token_registry()

    # Filter token pairs to only use funded tokens if wallet funding is enabled
    if config.wallet.funding_enabled and config.wallet.token_balances:
        funded_tokens = set(config.wallet.token_balances.keys())
        all_pairs = token_registry.get_all_pairs()
        filtered_pairs = [
            pair
            for pair in all_pairs
            if pair.sell_token.symbol in funded_tokens and pair.buy_token.symbol in funded_tokens
        ]

        # Create new registry with filtered pairs
        from cow_performance.load_generation.token_pair import TokenPairRegistry

        token_registry = TokenPairRegistry(token_pairs=filtered_pairs)

        if verbose and len(filtered_pairs) < len(all_pairs):
            console.print("[cyan]Token Pairs:[/cyan]")
            console.print(
                f"  Filtered to {len(filtered_pairs)} pairs using funded tokens: {', '.join(sorted(funded_tokens))}"
            )
            console.print()

    # Create trader pool based on wallet configuration
    trader_pool = create_trader_pool_from_config(config.wallet, num_traders)

    # Fund wallets if enabled (requires Anvil fork mode)
    if config.wallet.funding_enabled:
        if verbose:
            console.print("[bold cyan]Wallet Funding:[/bold cyan]")
            console.print(f"  RPC URL: {config.network.rpc_url}")
            console.print(f"  ETH per wallet: {config.wallet.eth_balance}")
            console.print(f"  Token balances: {config.wallet.token_balances}")

        try:
            # Connect to Web3
            web3 = Web3(Web3.HTTPProvider(config.network.rpc_url))
            if not web3.is_connected():
                raise ValueError(f"Failed to connect to RPC at {config.network.rpc_url}")

            if verbose:
                console.print(
                    f"  [green]✓[/green] Connected to RPC (chain ID: {web3.eth.chain_id})"
                )

            # Fund all traders in the pool
            fund_trader_pool(
                web3=web3,
                trader_pool=trader_pool,
                eth_balance=config.wallet.eth_balance,
                token_balances=config.wallet.token_balances,
                vault_relayer=config.network.vault_relayer,
            )

            if verbose:
                console.print(f"  [green]✓[/green] Funded {trader_pool.get_pool_size()} wallets")
                # Print wallet addresses for verification
                for i, trader in enumerate(trader_pool.get_all_traders()):
                    console.print(f"    Wallet {i+1}: {trader.address}")
                console.print()

        except Exception as e:
            console.print(f"[bold red]Error funding wallets:[/bold red] {e}")
            console.print(
                "[yellow]Hint: Wallet funding requires Anvil running in fork mode[/yellow]"
            )
            raise SystemExit(1) from None
    elif verbose and (config.wallet.private_keys or config.wallet.generate_count > 0):
        console.print("[bold cyan]Wallet Configuration:[/bold cyan]")
        if config.wallet.private_keys:
            console.print(f"  Using {len(config.wallet.private_keys)} provided private keys")
        elif config.wallet.generate_count > 0:
            console.print(f"  Generated {config.wallet.generate_count} new wallets")
        console.print("  [yellow]Note: Funding disabled. Wallets may not have balance.[/yellow]")
        console.print()

    # Create order factories
    # Set amount range based on wallet funding if enabled, otherwise use conservative defaults
    if config.wallet.funding_enabled:
        # Use 10-40% of minimum funded token balance to ensure fees are coverable
        # while avoiding insufficient balance errors
        min_token_balance = (
            min(config.wallet.token_balances.values()) if config.wallet.token_balances else 1.0
        )
        # Minimum 20% to ensure sell amount covers gas fees and provides enough trade value
        # Maximum 60% to use substantial amounts for better settlement viability
        amount_range = (min_token_balance * 0.2, min_token_balance * 0.6)
    else:
        # Conservative default for unfunded wallets
        amount_range = (0.01, 0.1)

    if verbose:
        console.print("[cyan]Order Configuration:[/cyan]")
        console.print(f"  Amount range: {amount_range[0]} - {amount_range[1]} tokens")
        console.print()

    # Create API client first (needed for quotes in OrderFactory)
    api_client = None
    if not dry_run:
        api_client = OrderbookClient(
            base_url=config.api.base_url,
            timeout=config.api.timeout,
            max_retries=config.api.max_retries,
        )

        if verbose:
            console.print(f"[cyan]API Client:[/cyan] {config.api.base_url}")
            # Check API health
            is_healthy = await api_client.check_health()
            if is_healthy:
                console.print("[green]✓[/green] Orderbook API is healthy")
            else:
                console.print("[yellow]⚠[/yellow] Warning: Could not reach orderbook API")
            console.print()

    order_factory = OrderFactory(
        token_pair_registry=token_registry,
        chain_id=config.network.chain_id,
        settlement_contract=config.network.settlement_contract,
        amount_range=amount_range,
        valid_duration=3600,  # 1 hour validity
        fee_percentage=0.0,  # Zero fees (CoW Protocol calculates fees automatically)
        api_client=api_client,  # Pass API client for getting quotes
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
    # Set max_poll_attempts based on settlement_wait_time to ensure
    # monitoring doesn't timeout before settlements can occur
    poll_interval = 5.0
    max_poll_attempts = int(settlement_wait_time / poll_interval) + 1
    order_tracker = OrderTracker(
        poll_interval=poll_interval,
        max_poll_attempts=max_poll_attempts,
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
        settlement_wait_time=float(settlement_wait_time),
    )

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
        order_cleanup_config=config.order_cleanup,
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
    settlement_wait: int | None = None,
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
        settlement_wait: Optional override for settlement wait time (seconds)
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
        # Merge verbose flag: CLI flag OR config setting
        use_verbose = verbose or config.output.verbose

        # Run the test
        metrics = asyncio.run(
            run_performance_test(
                config=config,
                traders=traders,
                duration=duration,
                settlement_wait=settlement_wait,
                verbose=use_verbose,
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
            # Table format is for console only, convert to JSON for file saving
            save_fmt = "json" if fmt == "table" else fmt

            if output_file:
                output_path = Path(output_file)
            else:
                # Auto-generate filename
                results_dir = config.output.results_dir
                results_dir.mkdir(parents=True, exist_ok=True)
                filename = create_result_filename(
                    prefix="perf-test",
                    output_format=save_fmt,
                )
                output_path = results_dir / filename

            save_metrics_to_file(metrics, save_fmt, output_path)
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
