# Claude Code Project Rules

## Documentation

- **The project can only have 1 README.md file** - All documentation must be consolidated in the root README.md file. Do not create separate README files in subdirectories.

## Code Quality

- **Always run linting after completing a feature** - After implementing or modifying any feature, you MUST run the full lint workflow to ensure code quality:
  ```bash
  # 1. Format code
  poetry run black src/ tests/ || .venv/bin/black src/ tests/

  # 2. Auto-fix linting errors
  poetry run ruff check --fix --unsafe-fixes src/ tests/ || .venv/bin/ruff check --fix --unsafe-fixes src/ tests/

  # 3. Check types
  poetry run mypy src/ || .venv/bin/mypy src/

  # 4. Run tests
  poetry run pytest || .venv/bin/pytest
  ```

- **Fix errors before committing** - Do not commit code with linting or type errors. All CI checks must pass.

- **Use the correct tool versions** - The project uses:
  - Black 23.12.0 (not the latest version on your system)
  - Ruff 0.14.13
  - MyPy 1.7+

  Always use Poetry or the virtual environment to ensure consistent versions with CI.
