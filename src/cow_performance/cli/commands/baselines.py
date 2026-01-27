"""Baseline management commands for performance testing.

This module provides basic baseline management functionality, with full
comparison and regression detection coming in M2-08.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

# Default directory for storing baselines
BASELINES_DIR = Path.home() / ".cow-perf" / "baselines"


def save_baseline(
    name: str,
    metrics: dict[str, Any],
    baselines_dir: Path | None = None,
) -> Path:
    """Save performance metrics as a baseline.

    Args:
        name: Baseline name
        metrics: Performance metrics to save
        baselines_dir: Optional directory for baselines (uses default if None)

    Returns:
        Path to saved baseline file

    Raises:
        ValueError: If baseline name is invalid
    """
    if not name or not name.strip():
        raise ValueError("Baseline name cannot be empty")

    # Use default directory if not specified
    if baselines_dir is None:
        baselines_dir = BASELINES_DIR

    # Ensure directory exists
    baselines_dir.mkdir(parents=True, exist_ok=True)

    # Create baseline data structure
    baseline_data = {
        "name": name,
        "timestamp": datetime.now().isoformat(),
        "metrics": metrics,
    }

    # Generate filename from name (sanitize)
    safe_name = name.replace(" ", "-").replace("/", "-")
    filename = f"{safe_name}.json"
    baseline_path = baselines_dir / filename

    # Save to file
    with open(baseline_path, "w") as f:
        json.dump(baseline_data, f, indent=2)

    return baseline_path


def load_baseline(
    name: str,
    baselines_dir: Path | None = None,
) -> dict[str, Any]:
    """Load a saved baseline.

    Args:
        name: Baseline name
        baselines_dir: Optional directory for baselines (uses default if None)

    Returns:
        Baseline data including metadata and metrics

    Raises:
        FileNotFoundError: If baseline doesn't exist
    """
    if baselines_dir is None:
        baselines_dir = BASELINES_DIR

    # Try to find baseline file
    safe_name = name.replace(" ", "-").replace("/", "-")
    baseline_path = baselines_dir / f"{safe_name}.json"

    if not baseline_path.exists():
        raise FileNotFoundError(f"Baseline not found: {name} (looking for {baseline_path})")

    with open(baseline_path, "r") as f:
        baseline_data = json.load(f)
        if not isinstance(baseline_data, dict):
            raise ValueError(f"Baseline file must contain a JSON object, got {type(baseline_data)}")
        return baseline_data


def list_baselines(baselines_dir: Path | None = None) -> list[dict[str, Any]]:
    """List all saved baselines.

    Args:
        baselines_dir: Optional directory for baselines (uses default if None)

    Returns:
        List of baseline metadata dictionaries
    """
    if baselines_dir is None:
        baselines_dir = BASELINES_DIR

    if not baselines_dir.exists():
        return []

    baselines = []

    for baseline_file in sorted(baselines_dir.glob("*.json")):
        try:
            with open(baseline_file, "r") as f:
                baseline_data = json.load(f)

            # Extract key metrics for summary
            metrics = baseline_data.get("metrics", {})
            orders = metrics.get("orders", {})
            performance = metrics.get("performance", {})

            baselines.append(
                {
                    "name": baseline_data.get("name", baseline_file.stem),
                    "timestamp": baseline_data.get("timestamp", "unknown"),
                    "file": baseline_file.name,
                    "total_orders": orders.get("total_submitted", 0),
                    "orders_per_second": performance.get("orders_per_second", 0.0),
                }
            )
        except Exception:
            # Skip invalid files
            continue

    return baselines


def delete_baseline(
    name: str,
    baselines_dir: Path | None = None,
) -> None:
    """Delete a saved baseline.

    Args:
        name: Baseline name
        baselines_dir: Optional directory for baselines (uses default if None)

    Raises:
        FileNotFoundError: If baseline doesn't exist
    """
    if baselines_dir is None:
        baselines_dir = BASELINES_DIR

    safe_name = name.replace(" ", "-").replace("/", "-")
    baseline_path = baselines_dir / f"{safe_name}.json"

    if not baseline_path.exists():
        raise FileNotFoundError(f"Baseline not found: {name}")

    baseline_path.unlink()


def save_baseline_command(
    name: str,
    results_file: Path,
    baselines_dir: Path | None = None,
) -> None:
    """Save a baseline from a results file.

    Args:
        name: Baseline name
        results_file: Path to results JSON file
        baselines_dir: Optional directory for baselines
    """
    console = Console()

    try:
        # Load results from file
        if not results_file.exists():
            console.print(f"[bold red]Error:[/bold red] Results file not found: {results_file}")
            raise SystemExit(2)

        with open(results_file, "r") as f:
            metrics = json.load(f)

        # Save as baseline
        baseline_path = save_baseline(name, metrics, baselines_dir)

        console.print(f"[bold green]✓[/bold green] Baseline saved: {name}")
        console.print(f"  Location: {baseline_path}")

    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise SystemExit(3) from None
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise SystemExit(1) from None


def show_baseline_command(
    name: str,
    baselines_dir: Path | None = None,
) -> None:
    """Show details of a saved baseline.

    Args:
        name: Baseline name
        baselines_dir: Optional directory for baselines
    """
    console = Console()

    try:
        baseline_data = load_baseline(name, baselines_dir)

        console.print(f"[bold cyan]Baseline:[/bold cyan] {baseline_data['name']}")
        console.print(f"[dim]Created: {baseline_data['timestamp']}[/dim]\n")

        # Extract metrics
        metrics = baseline_data.get("metrics", {})
        orchestration = metrics.get("orchestration", {})
        orders = metrics.get("orders", {})
        performance = metrics.get("performance", {})

        # Orchestration info
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Traders", str(orchestration.get("num_traders", 0)))
        table.add_row("Duration", f"{orchestration.get('duration', 0)}s")

        console.print(table)
        console.print()

        # Orders table
        table = Table(title="Orders", show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")

        table.add_row("Total Submitted", str(orders.get("total_submitted", 0)))
        table.add_row("Market Orders", str(orders.get("market_orders", 0)))
        table.add_row("Limit Orders", str(orders.get("limit_orders", 0)))
        table.add_row("TWAP Orders", str(orders.get("twap_orders", 0)))
        table.add_row("Stop-Loss Orders", str(orders.get("stop_loss_orders", 0)))
        table.add_row("Good-After-Time Orders", str(orders.get("good_after_time_orders", 0)))

        console.print(table)
        console.print()

        # Performance table
        table = Table(title="Performance", show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")

        table.add_row(
            "Orders per Second",
            f"{performance.get('orders_per_second', 0.0):.2f}",
        )
        table.add_row(
            "Avg Order Latency",
            f"{performance.get('avg_order_latency_ms', 0.0):.2f}ms",
        )

        console.print(table)

    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise SystemExit(2) from None
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise SystemExit(1) from None


def list_baselines_command(baselines_dir: Path | None = None) -> None:
    """List all saved baselines.

    Args:
        baselines_dir: Optional directory for baselines
    """
    console = Console()

    baselines = list_baselines(baselines_dir)

    if not baselines:
        console.print("[yellow]No baselines found.[/yellow]")
        console.print("\n[dim]Save a baseline with:[/dim]")
        console.print("  cow-perf run --save")
        console.print("  cow-perf baselines --save my-baseline results.json")
        return

    # Display baselines table
    table = Table(title="Saved Baselines", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="green")
    table.add_column("Created", style="dim")
    table.add_column("Orders", justify="right")
    table.add_column("Orders/sec", justify="right")

    for baseline in baselines:
        # Format timestamp
        try:
            timestamp = datetime.fromisoformat(baseline["timestamp"])
            timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M")
        except Exception:
            timestamp_str = baseline["timestamp"]

        table.add_row(
            baseline["name"],
            timestamp_str,
            str(baseline["total_orders"]),
            f"{baseline['orders_per_second']:.2f}",
        )

    console.print(table)


def delete_baseline_command(
    name: str,
    baselines_dir: Path | None = None,
) -> None:
    """Delete a saved baseline.

    Args:
        name: Baseline name
        baselines_dir: Optional directory for baselines
    """
    console = Console()

    try:
        delete_baseline(name, baselines_dir)
        console.print(f"[bold green]✓[/bold green] Baseline deleted: {name}")

    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise SystemExit(2) from None
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise SystemExit(1) from None
