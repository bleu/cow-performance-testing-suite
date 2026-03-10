"""Tests for environment variable substitution."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from cow_performance.scenarios.env_substitution import (
    EnvironmentSubstitutor,
    EnvSubstitutionError,
    load_dotenv_file,
    substitute_env_vars,
)


class TestEnvironmentSubstitutor:
    """Test EnvironmentSubstitutor class."""

    def test_simple_substitution(self):
        """Test simple environment variable substitution."""
        substitutor = EnvironmentSubstitutor(load_dotenv=False)
        substitutor.env_vars = {"API_URL": "http://localhost:8080", "PORT": "3000"}

        result = substitutor.substitute_string("Connect to ${API_URL} on port ${PORT}")

        assert result == "Connect to http://localhost:8080 on port 3000"

    def test_substitution_with_default(self):
        """Test substitution with default value."""
        substitutor = EnvironmentSubstitutor(load_dotenv=False)
        substitutor.env_vars = {}

        result = substitutor.substitute_string("${API_URL:-http://localhost:8080}")

        assert result == "http://localhost:8080"

    def test_substitution_with_default_override(self):
        """Test that environment variable overrides default value."""
        substitutor = EnvironmentSubstitutor(load_dotenv=False)
        substitutor.env_vars = {"API_URL": "http://production.com"}

        result = substitutor.substitute_string("${API_URL:-http://localhost:8080}")

        assert result == "http://production.com"

    def test_missing_required_variable(self):
        """Test error when required variable is missing."""
        substitutor = EnvironmentSubstitutor(load_dotenv=False)
        substitutor.env_vars = {}

        with pytest.raises(EnvSubstitutionError) as exc_info:
            substitutor.substitute_string("${MISSING_VAR}")

        assert "not found" in str(exc_info.value).lower()
        assert "MISSING_VAR" in str(exc_info.value)

    def test_multiple_substitutions(self):
        """Test multiple substitutions in one string."""
        substitutor = EnvironmentSubstitutor(load_dotenv=False)
        substitutor.env_vars = {
            "HOST": "example.com",
            "PORT": "8080",
            "PROTOCOL": "https",
        }

        result = substitutor.substitute_string("${PROTOCOL}://${HOST}:${PORT}/api")

        assert result == "https://example.com:8080/api"

    def test_mixed_substitution_with_defaults(self):
        """Test mixing required and optional variables."""
        substitutor = EnvironmentSubstitutor(load_dotenv=False)
        substitutor.env_vars = {"HOST": "example.com"}

        result = substitutor.substitute_string("${HOST}:${PORT:-8080}")

        assert result == "example.com:8080"

    def test_substitute_dict_simple(self):
        """Test dictionary substitution with string values."""
        substitutor = EnvironmentSubstitutor(load_dotenv=False)
        substitutor.env_vars = {"API_URL": "http://localhost:8080", "ENV": "dev"}

        config = {"api_url": "${API_URL}", "environment": "${ENV}", "timeout": 30}

        result = substitutor.substitute_dict(config)

        assert result == {
            "api_url": "http://localhost:8080",
            "environment": "dev",
            "timeout": 30,
        }

    def test_substitute_dict_nested(self):
        """Test nested dictionary substitution."""
        substitutor = EnvironmentSubstitutor(load_dotenv=False)
        substitutor.env_vars = {"DB_HOST": "localhost", "DB_PORT": "5432"}

        config = {
            "database": {
                "host": "${DB_HOST}",
                "port": "${DB_PORT:-5432}",
                "name": "testdb",
            },
            "timeout": 30,
        }

        result = substitutor.substitute_dict(config)

        assert result == {
            "database": {"host": "localhost", "port": "5432", "name": "testdb"},
            "timeout": 30,
        }

    def test_substitute_dict_with_list(self):
        """Test substitution in lists."""
        substitutor = EnvironmentSubstitutor(load_dotenv=False)
        substitutor.env_vars = {"TOKEN1": "WETH", "TOKEN2": "DAI"}

        config = {
            "tokens": ["${TOKEN1}", "${TOKEN2}", "USDC"],
            "count": 3,
        }

        result = substitutor.substitute_dict(config)

        assert result == {"tokens": ["WETH", "DAI", "USDC"], "count": 3}

    def test_substitute_dict_complex(self):
        """Test complex nested structure."""
        substitutor = EnvironmentSubstitutor(load_dotenv=False)
        substitutor.env_vars = {
            "ENV": "staging",
            "API_URL": "http://api.staging.com",
            "DB_HOST": "db.staging.com",
        }

        config = {
            "environment": "${ENV}",
            "api": {"url": "${API_URL}", "timeout": 30},
            "database": {
                "host": "${DB_HOST}",
                "replicas": ["${DB_HOST}-1", "${DB_HOST}-2"],
            },
        }

        result = substitutor.substitute_dict(config)

        assert result == {
            "environment": "staging",
            "api": {"url": "http://api.staging.com", "timeout": 30},
            "database": {
                "host": "db.staging.com",
                "replicas": ["db.staging.com-1", "db.staging.com-2"],
            },
        }

    def test_no_substitution_in_non_strings(self):
        """Test that non-string values are not modified."""
        substitutor = EnvironmentSubstitutor(load_dotenv=False)
        substitutor.env_vars = {"NUM": "42"}

        config = {
            "number": 42,
            "boolean": True,
            "null_value": None,
            "string_num": "${NUM}",
        }

        result = substitutor.substitute_dict(config)

        assert result == {
            "number": 42,
            "boolean": True,
            "null_value": None,
            "string_num": "42",
        }

    def test_default_with_spaces(self):
        """Test default values with spaces."""
        substitutor = EnvironmentSubstitutor(load_dotenv=False)
        substitutor.env_vars = {}

        result = substitutor.substitute_string("${DESC:-Default description with spaces}")

        assert result == "Default description with spaces"

    def test_env_var_with_special_chars_in_default(self):
        """Test default values with special characters."""
        substitutor = EnvironmentSubstitutor(load_dotenv=False)
        substitutor.env_vars = {}

        result = substitutor.substitute_string("${URL:-http://localhost:8080/api/v1}")

        assert result == "http://localhost:8080/api/v1"


class TestDotenvLoading:
    """Test .env file loading functionality."""

    def test_load_dotenv_basic(self, tmp_path):
        """Test loading basic .env file."""
        dotenv_file = tmp_path / ".env"
        dotenv_file.write_text("API_URL=http://localhost:8080\nPORT=3000\n")

        env_vars = load_dotenv_file(dotenv_file)

        assert env_vars == {"API_URL": "http://localhost:8080", "PORT": "3000"}

    def test_load_dotenv_with_quotes(self, tmp_path):
        """Test loading .env with quoted values."""
        dotenv_file = tmp_path / ".env"
        dotenv_file.write_text('API_URL="http://localhost:8080"\n' "DB_NAME='my_database'\n")

        env_vars = load_dotenv_file(dotenv_file)

        assert env_vars == {"API_URL": "http://localhost:8080", "DB_NAME": "my_database"}

    def test_load_dotenv_with_comments(self, tmp_path):
        """Test loading .env with comments."""
        dotenv_file = tmp_path / ".env"
        dotenv_file.write_text(
            "# This is a comment\n"
            "API_URL=http://localhost:8080\n"
            "# Another comment\n"
            "PORT=3000\n"
        )

        env_vars = load_dotenv_file(dotenv_file)

        assert env_vars == {"API_URL": "http://localhost:8080", "PORT": "3000"}

    def test_load_dotenv_with_empty_lines(self, tmp_path):
        """Test loading .env with empty lines."""
        dotenv_file = tmp_path / ".env"
        dotenv_file.write_text("API_URL=http://localhost:8080\n\nPORT=3000\n\n")

        env_vars = load_dotenv_file(dotenv_file)

        assert env_vars == {"API_URL": "http://localhost:8080", "PORT": "3000"}

    def test_load_dotenv_nonexistent(self):
        """Test loading nonexistent .env file."""
        env_vars = load_dotenv_file(Path("/nonexistent/.env"))

        assert env_vars == {}

    def test_substitutor_with_dotenv(self, tmp_path):
        """Test substitutor loading from .env file."""
        dotenv_file = tmp_path / ".env"
        dotenv_file.write_text("API_URL=http://localhost:8080\nENV=dev\n")

        substitutor = EnvironmentSubstitutor(load_dotenv=True, dotenv_path=dotenv_file)

        result = substitutor.substitute_string("${API_URL} in ${ENV}")

        assert result == "http://localhost:8080 in dev"

    def test_os_environ_overrides_dotenv(self, tmp_path):
        """Test that os.environ takes precedence over .env."""
        dotenv_file = tmp_path / ".env"
        dotenv_file.write_text("API_URL=http://localhost:8080\n")

        with patch.dict(os.environ, {"API_URL": "http://production.com"}):
            substitutor = EnvironmentSubstitutor(load_dotenv=True, dotenv_path=dotenv_file)

            result = substitutor.substitute_string("${API_URL}")

            assert result == "http://production.com"

    def test_dotenv_with_equals_in_value(self, tmp_path):
        """Test .env with equals signs in values."""
        dotenv_file = tmp_path / ".env"
        dotenv_file.write_text("CONNECTION_STRING=host=localhost;port=5432\n")

        env_vars = load_dotenv_file(dotenv_file)

        assert env_vars == {"CONNECTION_STRING": "host=localhost;port=5432"}


class TestSubstituteEnvVarsFunction:
    """Test convenience function for substitution."""

    def test_substitute_env_vars_without_dotenv(self):
        """Test convenience function without .env loading."""
        with patch.dict(os.environ, {"API_URL": "http://localhost:8080"}):
            config = {"api_url": "${API_URL}", "timeout": 30}

            result = substitute_env_vars(config, load_dotenv=False)

            assert result == {"api_url": "http://localhost:8080", "timeout": 30}

    def test_substitute_env_vars_with_dotenv(self, tmp_path):
        """Test convenience function with .env loading."""
        dotenv_file = tmp_path / ".env"
        dotenv_file.write_text("API_URL=http://localhost:8080\n")

        config = {"api_url": "${API_URL}", "timeout": 30}

        result = substitute_env_vars(config, load_dotenv=True, dotenv_path=dotenv_file)

        assert result == {"api_url": "http://localhost:8080", "timeout": 30}

    def test_substitute_env_vars_with_defaults(self):
        """Test convenience function with default values."""
        config = {
            "api_url": "${API_URL:-http://localhost:8080}",
            "env": "${ENV:-development}",
        }

        result = substitute_env_vars(config, load_dotenv=False)

        assert result == {
            "api_url": "http://localhost:8080",
            "env": "development",
        }


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_string(self):
        """Test substitution in empty string."""
        substitutor = EnvironmentSubstitutor(load_dotenv=False)
        substitutor.env_vars = {}

        result = substitutor.substitute_string("")

        assert result == ""

    def test_no_variables(self):
        """Test string with no variables."""
        substitutor = EnvironmentSubstitutor(load_dotenv=False)
        substitutor.env_vars = {}

        result = substitutor.substitute_string("Just a plain string")

        assert result == "Just a plain string"

    def test_empty_dict(self):
        """Test empty dictionary."""
        substitutor = EnvironmentSubstitutor(load_dotenv=False)
        substitutor.env_vars = {}

        result = substitutor.substitute_dict({})

        assert result == {}

    def test_variable_in_middle_of_string(self):
        """Test variable in the middle of text."""
        substitutor = EnvironmentSubstitutor(load_dotenv=False)
        substitutor.env_vars = {"VERSION": "1.2.3"}

        result = substitutor.substitute_string("API version ${VERSION} is ready")

        assert result == "API version 1.2.3 is ready"

    def test_multiple_occurrences_same_variable(self):
        """Test same variable appearing multiple times."""
        substitutor = EnvironmentSubstitutor(load_dotenv=False)
        substitutor.env_vars = {"TOKEN": "WETH"}

        result = substitutor.substitute_string("Buy ${TOKEN} or sell ${TOKEN}")

        assert result == "Buy WETH or sell WETH"

    def test_whitespace_in_variable_name(self):
        """Test handling of whitespace in variable expressions."""
        substitutor = EnvironmentSubstitutor(load_dotenv=False)
        substitutor.env_vars = {"API_URL": "http://localhost:8080"}

        # Whitespace should be trimmed
        result = substitutor.substitute_string("${ API_URL }")

        assert result == "http://localhost:8080"

    def test_whitespace_around_default(self):
        """Test handling of whitespace around default separator."""
        substitutor = EnvironmentSubstitutor(load_dotenv=False)
        substitutor.env_vars = {}

        result = substitutor.substitute_string("${ MISSING :- default value }")

        assert result == "default value"
