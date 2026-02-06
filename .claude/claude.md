# Claude Code Project Rules

## Before Starting Work

- **Check `thoughts/INDEX.md` first** - This index catalogs all existing plans, research, tickets, and prompts. Review it to avoid duplicating work that's already been done.

## Ticket & Task Management

- **NEVER update Linear directly** - Do not use Linear MCP tools to update ticket unless explicitly asked with words like "update Linear" or "sync to Linear"
- **Just "ticket" means the local file** - e.g., When asked to update a ticket, edit the file in `thoughts/tickets/`
- **Update the index when adding files** - When creating new files in `thoughts/`, add entries to `thoughts/INDEX.md`

## Documentation

- **The project can only have 1 README.md file** - All documentation must be consolidated in the root README.md file. Do not create separate README files in subdirectories.

## Code Quality

- **Run linting BEFORE each commit** - Run the full lint workflow on ALL of `src/` and `tests/` before EVERY commit, not just at the end of a feature:

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
