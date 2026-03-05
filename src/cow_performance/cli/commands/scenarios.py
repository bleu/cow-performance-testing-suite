"""Scenario management commands for performance testing.

This module provides the foundation for scenario management, with full
implementation coming in M1-06.
"""

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field, field_validator
from rich.console import Console
from rich.table import Table


class ResourceRequirements(BaseModel):
    """Resource requirements for a scenario."""

    min_memory_gb: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Minimum memory required in GB",
    )
    min_cpu_cores: Optional[int] = Field(
        default=None,
        ge=1,
        description="Minimum CPU cores required",
    )
    recommended_memory_gb: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Recommended memory in GB",
    )
    recommended_cpu_cores: Optional[int] = Field(
        default=None,
        ge=1,
        description="Recommended CPU cores",
    )


class ScenarioMetadata(BaseModel):
    """Metadata about a scenario including expected outcomes and resource requirements."""

    expected_orders: Optional[int] = Field(
        default=None,
        ge=0,
        description="Expected number of orders for this scenario",
    )
    expected_duration_seconds: Optional[int] = Field(
        default=None,
        ge=1,
        description="Expected test duration in seconds",
    )
    resources: Optional[ResourceRequirements] = Field(
        default=None,
        description="Resource requirements for this scenario",
    )


class SuccessCriteria(BaseModel):
    """Success criteria for validating test results."""

    min_success_rate: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimum order success rate (0.0-1.0)",
    )
    max_p95_latency_seconds: Optional[float] = Field(
        default=None,
        gt=0.0,
        description="Maximum P95 latency in seconds",
    )
    max_error_rate: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Maximum error rate (0.0-1.0)",
    )
    min_throughput_per_second: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Minimum throughput in orders per second",
    )


class ScenarioConfig(BaseModel):
    """Configuration for a performance test scenario.

    This defines the parameters for a complete performance test scenario,
    including trader behavior and order type distribution.
    """

    name: str = Field(description="Scenario name")
    description: str = Field(default="", description="Scenario description")
    version: str = Field(default="1.0", description="Scenario version")
    tags: list[str] = Field(
        default_factory=list,
        description="Tags for categorizing the scenario (e.g., 'stress', 'baseline', 'short')",
    )

    # Metadata about expected outcomes and resource requirements
    metadata: Optional[ScenarioMetadata] = Field(
        default=None,
        description="Scenario metadata including expected orders and resource requirements",
    )

    # Success criteria for automated validation
    success_criteria: Optional[SuccessCriteria] = Field(
        default=None,
        description="Success criteria for validating test results",
    )

    # Trader configuration
    num_traders: int = Field(default=10, ge=1, description="Number of concurrent traders")
    duration: int = Field(default=60, ge=1, description="Test duration in seconds")
    startup_interval: float = Field(
        default=0.1,
        ge=0.0,
        description="Interval between trader startups",
    )

    # Order type ratios (must sum to 1.0)
    market_order_ratio: float = Field(default=0.4, ge=0.0, le=1.0)
    limit_order_ratio: float = Field(default=0.4, ge=0.0, le=1.0)
    twap_order_ratio: float = Field(default=0.1, ge=0.0, le=1.0)
    stop_loss_order_ratio: float = Field(default=0.05, ge=0.0, le=1.0)
    good_after_time_order_ratio: float = Field(default=0.05, ge=0.0, le=1.0)

    # Trading pattern
    trading_pattern: str = Field(
        default="constant_rate",
        description="Trading pattern (constant_rate, burst, random_interval)",
    )
    base_rate: float = Field(
        default=60.0,
        gt=0.0,
        description="Base trading rate (orders per minute) for constant_rate pattern",
    )

    # Burst pattern parameters (optional)
    burst_size: int | None = Field(
        default=None,
        ge=1,
        description="Number of orders per burst (for burst pattern)",
    )
    burst_interval: float | None = Field(
        default=None,
        gt=0.0,
        description="Interval between orders in burst (for burst pattern)",
    )
    quiet_period: float | None = Field(
        default=None,
        gt=0.0,
        description="Quiet period between bursts (for burst pattern)",
    )

    # Random interval parameters (optional)
    min_interval: float | None = Field(
        default=None,
        ge=0.0,
        description="Minimum interval between orders (for random_interval pattern)",
    )
    max_interval: float | None = Field(
        default=None,
        gt=0.0,
        description="Maximum interval between orders (for random_interval pattern)",
    )

    @field_validator("trading_pattern")
    @classmethod
    def validate_trading_pattern(cls, v: str) -> str:
        """Validate trading pattern."""
        allowed = ["constant_rate", "burst", "random_interval"]
        if v not in allowed:
            raise ValueError(f"Trading pattern must be one of: {', '.join(allowed)}, got: {v}")
        return v

    def validate_ratios(self) -> None:
        """Validate that order type ratios sum to 1.0."""
        total = (
            self.market_order_ratio
            + self.limit_order_ratio
            + self.twap_order_ratio
            + self.stop_loss_order_ratio
            + self.good_after_time_order_ratio
        )
        if abs(total - 1.0) > 0.001:  # Allow for floating point precision
            raise ValueError(
                f"Order type ratios must sum to 1.0, got {total}. "
                f"Current ratios: market={self.market_order_ratio}, "
                f"limit={self.limit_order_ratio}, twap={self.twap_order_ratio}, "
                f"stop_loss={self.stop_loss_order_ratio}, "
                f"good_after_time={self.good_after_time_order_ratio}"
            )

    def validate_pattern_parameters(self) -> None:
        """Validate that required parameters for trading pattern are present."""
        if self.trading_pattern == "burst":
            if self.burst_size is None:
                raise ValueError("burst_size is required for burst pattern")
            if self.burst_interval is None:
                raise ValueError("burst_interval is required for burst pattern")
            if self.quiet_period is None:
                raise ValueError("quiet_period is required for burst pattern")

        if self.trading_pattern == "random_interval":
            if self.min_interval is None:
                raise ValueError("min_interval is required for random_interval pattern")
            if self.max_interval is None:
                raise ValueError("max_interval is required for random_interval pattern")
            if self.min_interval >= self.max_interval:
                raise ValueError("min_interval must be less than max_interval")


def load_scenario_from_yaml(scenario_path: Path) -> ScenarioConfig:
    """Load scenario configuration from YAML file.

    Args:
        scenario_path: Path to scenario YAML file

    Returns:
        Parsed and validated ScenarioConfig

    Raises:
        FileNotFoundError: If scenario file doesn't exist
        ValueError: If scenario configuration is invalid
        yaml.YAMLError: If YAML is malformed
    """
    if not scenario_path.exists():
        raise FileNotFoundError(f"Scenario file not found: {scenario_path}")

    with open(scenario_path, "r") as f:
        scenario_data = yaml.safe_load(f)

    if scenario_data is None:
        raise ValueError(f"Scenario file is empty: {scenario_path}")

    # Parse and validate
    scenario = ScenarioConfig(**scenario_data)
    scenario.validate_ratios()
    scenario.validate_pattern_parameters()

    return scenario


def save_scenario_to_yaml(scenario: ScenarioConfig, output_path: Path) -> None:
    """Save scenario configuration to YAML file.

    Args:
        scenario: Scenario configuration to save
        output_path: Path where to save the scenario
    """
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to dictionary
    scenario_data = scenario.model_dump(exclude_none=True)

    with open(output_path, "w") as f:
        yaml.dump(scenario_data, f, default_flow_style=False, sort_keys=False)


def create_scenario_template() -> str:
    """Create a scenario template string.

    Returns:
        YAML string with scenario template
    """
    template = """# Performance Test Scenario Configuration

# Scenario metadata
name: "example-scenario"
description: "Example performance test scenario"

# Trader configuration
num_traders: 10
duration: 60  # seconds
startup_interval: 0.1

# Order type distribution (must sum to 1.0)
market_order_ratio: 0.4
limit_order_ratio: 0.4
twap_order_ratio: 0.1
stop_loss_order_ratio: 0.05
good_after_time_order_ratio: 0.05

# Trading pattern
trading_pattern: "constant_rate"  # constant_rate, burst, or random_interval
base_rate: 60.0  # orders per minute (for constant_rate)

# Burst pattern parameters (uncomment if using burst pattern)
# burst_size: 5
# burst_interval: 0.1
# quiet_period: 5.0

# Random interval parameters (uncomment if using random_interval)
# min_interval: 0.5
# max_interval: 3.0
"""
    return template


def list_scenarios_command(scenarios_dir: Path | None = None) -> None:
    """List available scenarios.

    Args:
        scenarios_dir: Optional directory to search for scenarios
    """
    console = Console()

    if scenarios_dir is None:
        scenarios_dir = Path(".cow-perf") / "scenarios"

    console.print(f"[bold cyan]Scenarios Directory:[/bold cyan] {scenarios_dir}\n")

    if not scenarios_dir.exists():
        console.print("[yellow]No scenarios directory found. " "Create scenarios with:[/yellow]")
        console.print("  cow-perf scenarios --create-template my-scenario.yml")
        return

    # Find all YAML files
    scenario_files = list(scenarios_dir.glob("*.yml")) + list(scenarios_dir.glob("*.yaml"))

    if not scenario_files:
        console.print("[yellow]No scenario files found.[/yellow]")
        return

    # Load and display scenarios
    table = Table(title="Available Scenarios", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="green")
    table.add_column("Traders", justify="right")
    table.add_column("Duration", justify="right")
    table.add_column("Pattern", style="cyan")
    table.add_column("File", style="dim")

    for scenario_file in sorted(scenario_files):
        try:
            scenario = load_scenario_from_yaml(scenario_file)
            table.add_row(
                scenario.name,
                str(scenario.num_traders),
                f"{scenario.duration}s",
                scenario.trading_pattern,
                scenario_file.name,
            )
        except Exception as e:
            # Show error for invalid scenarios
            table.add_row(
                "[red]ERROR[/red]",
                "-",
                "-",
                "-",
                f"{scenario_file.name}: {str(e)[:40]}...",
            )

    console.print(table)


def validate_scenario_command(scenario_path: Path) -> None:
    """Validate a scenario configuration file.

    Args:
        scenario_path: Path to scenario file to validate
    """
    console = Console()

    try:
        scenario = load_scenario_from_yaml(scenario_path)

        console.print("[bold green]✓[/bold green] Scenario is valid!")
        console.print()

        # Display scenario details
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Name", scenario.name)
        table.add_row("Description", scenario.description or "-")
        table.add_row("Version", scenario.version)
        if scenario.tags:
            table.add_row("Tags", ", ".join(scenario.tags))
        table.add_row("Traders", str(scenario.num_traders))
        table.add_row("Duration", f"{scenario.duration}s")
        table.add_row("Trading Pattern", scenario.trading_pattern)

        console.print(table)
        console.print()

        # Metadata (if present)
        if scenario.metadata:
            metadata_table = Table(
                title="Scenario Metadata", show_header=True, header_style="bold cyan"
            )
            metadata_table.add_column("Property", style="cyan")
            metadata_table.add_column("Value", style="green")

            if scenario.metadata.expected_orders is not None:
                metadata_table.add_row("Expected Orders", str(scenario.metadata.expected_orders))
            if scenario.metadata.expected_duration_seconds is not None:
                metadata_table.add_row(
                    "Expected Duration", f"{scenario.metadata.expected_duration_seconds}s"
                )

            if scenario.metadata.resources:
                res = scenario.metadata.resources
                if res.min_memory_gb is not None:
                    metadata_table.add_row("Min Memory", f"{res.min_memory_gb}GB")
                if res.min_cpu_cores is not None:
                    metadata_table.add_row("Min CPU Cores", str(res.min_cpu_cores))
                if res.recommended_memory_gb is not None:
                    metadata_table.add_row("Recommended Memory", f"{res.recommended_memory_gb}GB")
                if res.recommended_cpu_cores is not None:
                    metadata_table.add_row("Recommended CPU Cores", str(res.recommended_cpu_cores))

            console.print(metadata_table)
            console.print()

        # Success criteria (if present)
        if scenario.success_criteria:
            criteria_table = Table(
                title="Success Criteria", show_header=True, header_style="bold cyan"
            )
            criteria_table.add_column("Criterion", style="cyan")
            criteria_table.add_column("Value", style="green")

            crit = scenario.success_criteria
            if crit.min_success_rate is not None:
                criteria_table.add_row("Min Success Rate", f"{crit.min_success_rate:.1%}")
            if crit.max_p95_latency_seconds is not None:
                criteria_table.add_row("Max P95 Latency", f"{crit.max_p95_latency_seconds}s")
            if crit.max_error_rate is not None:
                criteria_table.add_row("Max Error Rate", f"{crit.max_error_rate:.1%}")
            if crit.min_throughput_per_second is not None:
                criteria_table.add_row(
                    "Min Throughput", f"{crit.min_throughput_per_second} orders/s"
                )

            console.print(criteria_table)
            console.print()

        # Order type distribution
        table = Table(title="Order Type Distribution", show_header=True, header_style="bold cyan")
        table.add_column("Order Type", style="cyan")
        table.add_column("Ratio", style="green", justify="right")

        table.add_row("Market", f"{scenario.market_order_ratio:.1%}")
        table.add_row("Limit", f"{scenario.limit_order_ratio:.1%}")
        table.add_row("TWAP", f"{scenario.twap_order_ratio:.1%}")
        table.add_row("Stop-Loss", f"{scenario.stop_loss_order_ratio:.1%}")
        table.add_row("Good-After-Time", f"{scenario.good_after_time_order_ratio:.1%}")

        console.print(table)

    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise SystemExit(2) from None
    except ValueError as e:
        console.print(f"[bold red]Validation Error:[/bold red] {e}")
        raise SystemExit(3) from None
    except yaml.YAMLError as e:
        console.print(f"[bold red]YAML Error:[/bold red] {e}")
        raise SystemExit(3) from None
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise SystemExit(1) from None
