"""Main CLI entry point for the CoW Performance Testing Suite."""

from typing import Optional

import typer
from rich.console import Console

app = typer.Typer(
    name="cow-perf",
    help="CoW Protocol Performance Testing Suite",
    add_completion=False,
)

console = Console()


@app.callback()
def main() -> None:
    """
    CoW Protocol Performance Testing Suite.

    A comprehensive tool for load testing and benchmarking the CoW Protocol Playground.
    """
    pass


@app.command(name="version")
def show_version() -> None:
    """Show version and exit."""
    console.print("[bold green]CoW Performance Testing Suite[/bold green] v0.1.0")


@app.command()
def run(
    scenario: str,
    duration: Optional[int] = typer.Option(None, "--duration", "-d", help="Override scenario duration (seconds)"),
) -> None:
    """Run a performance test scenario.

    Args:
        scenario: Scenario name or path to scenario file
        duration: Override scenario duration (seconds)
    """
    console.print(f"[bold green]Running scenario:[/bold green] {scenario}")
    if duration:
        console.print(f"[bold yellow]Duration override:[/bold yellow] {duration}s")
    console.print("\n[yellow]Note: Full implementation coming in M1-03[/yellow]")


@app.command()
def scenarios() -> None:
    """List available test scenarios."""
    console.print("[bold green]Available scenarios:[/bold green]")
    console.print("\n[yellow]Scenario library coming in M4-14[/yellow]")


@app.command()
def baselines() -> None:
    """Manage performance baselines."""
    console.print("[bold green]Baseline management:[/bold green]")
    console.print("\n[yellow]Baseline system coming in M2-08[/yellow]")


@app.command()
def config() -> None:
    """Show current configuration."""
    console.print("[bold green]Configuration:[/bold green]")
    console.print("\n[yellow]Configuration system coming in M4-15[/yellow]")


if __name__ == "__main__":
    app()
