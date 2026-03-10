"""Environment variable substitution for configuration files.

This module provides advanced environment variable substitution with support for:
- Simple references: ${VAR_NAME}
- Default values: ${VAR_NAME:-default_value}
- .env file loading
- Nested substitution in configuration dictionaries
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any


class EnvSubstitutionError(Exception):
    """Error during environment variable substitution."""

    pass


class EnvironmentSubstitutor:
    """Handles environment variable substitution in configuration strings and structures."""

    # Pattern to match ${VAR_NAME} or ${VAR_NAME:-default}
    ENV_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")

    def __init__(self, load_dotenv: bool = True, dotenv_path: Path | None = None) -> None:
        """Initialize environment substitutor.

        Args:
            load_dotenv: Whether to load .env file (default: True)
            dotenv_path: Path to .env file (default: .env in current directory)
        """
        self.env_vars: dict[str, str] = {}

        # Load .env file if requested
        if load_dotenv:
            self._load_dotenv(dotenv_path)

        # Merge with os.environ (os.environ takes precedence)
        self.env_vars.update(os.environ)

    def _load_dotenv(self, dotenv_path: Path | None = None) -> None:
        """Load environment variables from .env file.

        Args:
            dotenv_path: Path to .env file (default: .env in current directory)
        """
        if dotenv_path is None:
            dotenv_path = Path(".env")

        if not dotenv_path.exists():
            # .env is optional, don't error if not found
            return

        try:
            with open(dotenv_path) as f:
                for _line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue

                    # Parse KEY=VALUE format
                    if "=" not in line:
                        continue

                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()

                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]

                    self.env_vars[key] = value

        except Exception as e:
            raise EnvSubstitutionError(f"Failed to load .env file from {dotenv_path}: {e}") from e

    def substitute_string(self, text: str) -> str:
        """Substitute environment variables in a string.

        Supports:
        - ${VAR_NAME} - Simple substitution (errors if not found)
        - ${VAR_NAME:-default} - Substitution with default value

        Args:
            text: String containing environment variable references

        Returns:
            String with environment variables substituted

        Raises:
            EnvSubstitutionError: If a required variable is not found
        """

        def replace_match(match: re.Match[str]) -> str:
            var_expr = match.group(1)

            # Check for default value syntax: VAR_NAME:-default
            if ":-" in var_expr:
                var_name, default_value = var_expr.split(":-", 1)
                var_name = var_name.strip()
                default_value = default_value.strip()

                # Return env var or default
                return self.env_vars.get(var_name, default_value)
            else:
                # No default - variable is required
                var_name = var_expr.strip()

                if var_name not in self.env_vars:
                    raise EnvSubstitutionError(
                        f"Environment variable not found: {var_name}\n"
                        f"Available variables: {', '.join(sorted(self.env_vars.keys())[:10])}"
                        f"{'...' if len(self.env_vars) > 10 else ''}"
                    )

                return self.env_vars[var_name]

        try:
            return self.ENV_VAR_PATTERN.sub(replace_match, text)
        except EnvSubstitutionError:
            raise
        except Exception as e:
            raise EnvSubstitutionError(f"Failed to substitute environment variables: {e}") from e

    def substitute_dict(self, config: dict[str, Any]) -> dict[str, Any]:
        """Recursively substitute environment variables in a configuration dictionary.

        Only substitutes in string values, not in keys or structural elements.

        Args:
            config: Configuration dictionary

        Returns:
            Configuration dictionary with substituted values
        """
        result: dict[str, Any] = {}

        for key, value in config.items():
            if isinstance(value, str):
                # Substitute in string values
                result[key] = self.substitute_string(value)
            elif isinstance(value, dict):
                # Recursively process nested dictionaries
                result[key] = self.substitute_dict(value)
            elif isinstance(value, list):
                # Process lists
                result[key] = self._substitute_list(value)
            else:
                # Leave other types unchanged
                result[key] = value

        return result

    def _substitute_list(self, items: list[Any]) -> list[Any]:
        """Recursively substitute environment variables in a list.

        Args:
            items: List of items

        Returns:
            List with substituted values
        """
        result: list[Any] = []

        for item in items:
            if isinstance(item, str):
                result.append(self.substitute_string(item))
            elif isinstance(item, dict):
                result.append(self.substitute_dict(item))
            elif isinstance(item, list):
                result.append(self._substitute_list(item))
            else:
                result.append(item)

        return result


def load_dotenv_file(dotenv_path: Path | None = None) -> dict[str, str]:
    """Load environment variables from .env file.

    Args:
        dotenv_path: Path to .env file (default: .env in current directory)

    Returns:
        Dictionary of environment variables

    Raises:
        EnvSubstitutionError: If .env file cannot be loaded
    """
    if dotenv_path is None:
        dotenv_path = Path(".env")

    if not dotenv_path.exists():
        return {}

    env_vars: dict[str, str] = {}

    try:
        with open(dotenv_path) as f:
            for _line_num, line in enumerate(f, 1):
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                # Parse KEY=VALUE format
                if "=" not in line:
                    continue

                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]

                env_vars[key] = value

    except Exception as e:
        raise EnvSubstitutionError(f"Failed to load .env file from {dotenv_path}: {e}") from e

    return env_vars


def substitute_env_vars(
    config: dict[str, Any],
    load_dotenv: bool = True,
    dotenv_path: Path | None = None,
) -> dict[str, Any]:
    """Convenience function to substitute environment variables in a configuration dictionary.

    Args:
        config: Configuration dictionary
        load_dotenv: Whether to load .env file (default: True)
        dotenv_path: Path to .env file (default: .env in current directory)

    Returns:
        Configuration dictionary with substituted values

    Raises:
        EnvSubstitutionError: If substitution fails
    """
    substitutor = EnvironmentSubstitutor(load_dotenv=load_dotenv, dotenv_path=dotenv_path)
    return substitutor.substitute_dict(config)
