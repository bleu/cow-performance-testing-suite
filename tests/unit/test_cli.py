"""Unit tests for CLI commands."""

from typer.testing import CliRunner

from cow_performance.cli.main import app

runner = CliRunner()


class TestCLI:
    """Test CLI commands."""

    def test_version_command(self) -> None:
        """Test version command."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "CoW Performance Testing Suite" in result.stdout
        assert "0.1.0" in result.stdout

    def test_run_command_executes(self) -> None:
        """Test that run command executes with a scenario."""
        result = runner.invoke(app, ["run", "test-scenario"])
        assert result.exit_code == 0
        assert "Running scenario: test-scenario" in result.stdout
        assert "Full implementation coming in M1-03" in result.stdout

    def test_scenarios_command_executes(self) -> None:
        """Test that scenarios command executes."""
        result = runner.invoke(app, ["scenarios"])
        assert result.exit_code == 0
        assert "Available scenarios" in result.stdout
        assert "Scenario library coming in M4-14" in result.stdout

    def test_baselines_command_executes(self) -> None:
        """Test that baselines command executes."""
        result = runner.invoke(app, ["baselines"])
        assert result.exit_code == 0
        assert "Baseline management" in result.stdout
        assert "Baseline system coming in M2-08" in result.stdout

    def test_config_command_executes(self) -> None:
        """Test that config command executes."""
        result = runner.invoke(app, ["config"])
        assert result.exit_code == 0
        assert "Configuration" in result.stdout
        assert "Configuration system coming in M4-15" in result.stdout
