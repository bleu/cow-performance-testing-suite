# Development Guide

This guide covers the development setup, coding standards, testing practices, and contribution guidelines for the CoW Performance Testing Suite.

## Development Environment Setup

### Prerequisites

- Python 3.11 or higher
- Poetry 1.7.1 or higher
- Git
- Docker and Docker Compose (for integration tests)
- A code editor (VS Code, PyCharm, etc.)

### Initial Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/cowprotocol/cow-performance-testing-suite.git
   cd cow-performance-testing-suite
   ```

2. **Install Poetry** (if not installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Install dependencies:**
   ```bash
   poetry install --with dev
   ```

4. **Activate the virtual environment:**
   ```bash
   poetry shell
   ```

5. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

6. **Verify the setup:**
   ```bash
   # Run tests
   pytest

   # Run linters
   black --check src/ tests/
   ruff check src/ tests/
   mypy src/
   ```

### IDE Configuration

#### VS Code

Recommended extensions:
- Python (Microsoft)
- Pylance
- Ruff
- Black Formatter

Settings (`.vscode/settings.json`):
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.testing.pytestEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

#### PyCharm

1. Configure Poetry interpreter:
   - File → Settings → Project → Python Interpreter
   - Add Interpreter → Poetry Environment
   - Select existing environment: `.venv`

2. Enable tools:
   - File → Settings → Tools → Black
   - File → Settings → Tools → External Tools (add Ruff)

## Coding Standards

### Code Style

We follow PEP 8 with some modifications:

- **Line length**: 100 characters (not 79)
- **Quotes**: Double quotes for strings (enforced by Black)
- **Imports**: Organized with isort (via Ruff)

### Type Hints

**All functions must have type hints:**

```python
# Good
def calculate_latency(start: float, end: float) -> float:
    return end - start

# Bad
def calculate_latency(start, end):
    return end - start
```

**Use modern type hint syntax (Python 3.11+):**

```python
# Good (Python 3.11+)
def process_orders(orders: list[Order]) -> dict[str, int]:
    pass

# Avoid (old syntax)
from typing import List, Dict
def process_orders(orders: List[Order]) -> Dict[str, int]:
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def submit_order(
    order: Order,
    api_client: APIClient,
    timeout: float = 30.0,
) -> OrderResponse:
    """Submit an order to the orderbook API.

    Args:
        order: The order to submit
        api_client: HTTP client for API requests
        timeout: Request timeout in seconds

    Returns:
        Response from the orderbook API

    Raises:
        APIError: If the API request fails
        TimeoutError: If the request times out
    """
    pass
```

### Async Code

Follow async best practices:

```python
# Good: Use async/await consistently
async def fetch_order_status(order_uid: str) -> OrderStatus:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"/api/orders/{order_uid}") as response:
            return await response.json()

# Avoid: Blocking calls in async functions
async def bad_example():
    time.sleep(1)  # ❌ Blocks the event loop
    await asyncio.sleep(1)  # ✓ Correct

# Use asyncio.gather for concurrent operations
async def fetch_multiple_orders(order_uids: list[str]) -> list[OrderStatus]:
    tasks = [fetch_order_status(uid) for uid in order_uids]
    return await asyncio.gather(*tasks)
```

### Error Handling

```python
# Define custom exceptions
class PerformanceTestError(Exception):
    """Base exception for performance testing"""
    pass

class OrderSubmissionError(PerformanceTestError):
    """Raised when order submission fails"""
    pass

# Use specific exceptions
async def submit_order(order: Order) -> OrderResponse:
    try:
        response = await api_client.post("/orders", order.dict())
    except aiohttp.ClientError as e:
        raise OrderSubmissionError(f"Failed to submit order: {e}") from e

    if response.status != 201:
        raise OrderSubmissionError(
            f"Order rejected: {response.status} {await response.text()}"
        )

    return OrderResponse(**await response.json())
```

### Configuration Management

Use Pydantic for configuration:

```python
from pydantic import BaseModel, Field

class SubmissionStrategyConfig(BaseModel):
    """Configuration for order submission strategy"""

    type: str = Field(description="Strategy type")
    rate: float = Field(gt=0, description="Orders per second")
    jitter: float = Field(default=0.0, ge=0, description="Timing jitter")

    class Config:
        extra = "forbid"  # Reject unknown fields
```

## Testing

### Test Organization

```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_order_factory.py
│   ├── test_strategies.py
│   └── ...
├── integration/             # Integration tests (slower, use services)
│   ├── test_api_client.py
│   ├── test_scenario_execution.py
│   └── ...
└── conftest.py             # Shared fixtures
```

### Writing Unit Tests

```python
import pytest
from cow_performance.load_generation import OrderFactory

class TestOrderFactory:
    """Unit tests for OrderFactory"""

    def test_create_market_order(self):
        """Test creating a market order"""
        factory = OrderFactory()
        order = factory.create_market_order(
            sell_token="WETH",
            buy_token="DAI",
            sell_amount=1000000000000000000,  # 1 ETH
        )

        assert order.kind == "sell"
        assert order.sell_token == "WETH"
        assert order.buy_token == "DAI"

    @pytest.mark.asyncio
    async def test_order_signing(self):
        """Test EIP-712 order signing"""
        # Test implementation
        pass
```

### Writing Integration Tests

```python
import pytest
from cow_performance.scenarios import ScenarioExecutor

@pytest.mark.integration
@pytest.mark.asyncio
async def test_light_load_scenario(orderbook_api_url):
    """Test light load scenario execution"""
    scenario = load_scenario("light-load")
    executor = ScenarioExecutor(scenario)

    result = await executor.execute()

    assert result.success_rate > 0.95
    assert result.total_orders_submitted > 0
```

### Test Fixtures

Define reusable fixtures in `conftest.py`:

```python
import pytest
from cow_performance.load_generation import TraderPool

@pytest.fixture
def trader_pool():
    """Create a trader pool for testing"""
    pool = TraderPool(num_traders=5)
    pool.initialize()
    return pool

@pytest.fixture
def mock_api_client(monkeypatch):
    """Mock API client for testing without real API calls"""
    # Mock implementation
    pass
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_order_factory.py

# Run specific test
pytest tests/unit/test_order_factory.py::TestOrderFactory::test_create_market_order

# Run with coverage
pytest --cov=src/cow_performance --cov-report=html

# Run only unit tests
pytest tests/unit

# Run only integration tests
pytest tests/integration -m integration

# Run in parallel (faster)
pytest -n auto

# Run with verbose output
pytest -v

# Show print statements
pytest -s
```

### Test Markers

Use markers to categorize tests:

```python
import pytest

@pytest.mark.unit
def test_fast_unit():
    pass

@pytest.mark.integration
@pytest.mark.slow
async def test_slow_integration():
    pass
```

Run specific markers:
```bash
pytest -m unit          # Run only unit tests
pytest -m "not slow"    # Skip slow tests
pytest -m integration   # Run integration tests only
```

## Code Quality Tools

### Black (Code Formatting)

```bash
# Format code
black src/ tests/

# Check without modifying
black --check src/ tests/

# Show what would change
black --diff src/ tests/
```

### Ruff (Linting)

```bash
# Lint code
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/

# Show rule details
ruff rule E501
```

### MyPy (Type Checking)

```bash
# Type check
mypy src/

# Type check with strict mode
mypy --strict src/

# Check specific file
mypy src/cow_performance/cli/main.py
```

### Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`:

```bash
# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files

# Skip hooks (not recommended)
git commit --no-verify
```

## Git Workflow

### Branch Naming

- Feature: `feature/description`
- Bugfix: `fix/description`
- Documentation: `docs/description`
- Release: `release/vX.Y.Z`

Examples:
- `feature/add-spike-strategy`
- `fix/order-signing-bug`
- `docs/update-architecture`

### Commit Messages

Follow conventional commits:

```
type(scope): short description

Longer description if needed.

- Bullet points for details
- More context

Fixes #123
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring
- `chore`: Maintenance

Examples:
```
feat(cli): add scenario list command

Add 'cow-perf scenarios list' command to display available
scenarios with descriptions and tags.

- Implemented ScenarioLister class
- Added table formatting with rich
- Updated CLI documentation

Closes #45
```

### Pull Request Process

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes and commit:**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

3. **Keep branch up to date:**
   ```bash
   git fetch origin
   git rebase origin/main
   ```

4. **Push and create PR:**
   ```bash
   git push origin feature/my-feature
   ```

5. **PR Checklist:**
   - [ ] Tests pass locally
   - [ ] Code is formatted (black)
   - [ ] Linting passes (ruff)
   - [ ] Type checking passes (mypy)
   - [ ] Tests added for new functionality
   - [ ] Documentation updated
   - [ ] Commit messages follow conventions

## Debugging

### Using debugger

```python
# Built-in debugger
import pdb; pdb.set_trace()

# Or use breakpoint() (Python 3.7+)
breakpoint()
```

### Logging

Use the logging module:

```python
import logging

logger = logging.getLogger(__name__)

def submit_order(order: Order) -> None:
    logger.debug(f"Submitting order: {order.uid}")
    try:
        # ... submit order
        logger.info(f"Order submitted successfully: {order.uid}")
    except Exception as e:
        logger.error(f"Failed to submit order {order.uid}: {e}", exc_info=True)
```

### Pytest Debugging

```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger on first failure
pytest -x --pdb

# Show local variables in traceback
pytest -l

# Verbose output
pytest -vv
```

## Performance Profiling

### Using cProfile

```bash
python -m cProfile -o output.prof -m cow_performance.cli.main run --scenario light-load
```

### Using line_profiler

```python
from line_profiler import profile

@profile
def expensive_function():
    # ... code to profile
    pass
```

## Documentation

### Updating Documentation

- Keep `README.md` up to date
- Update `docs/architecture.md` for design changes
- Update `docs/development.md` (this file) for workflow changes
- Add docstrings to new functions and classes

### Building Documentation

```bash
# Install documentation dependencies
poetry install --with docs

# Build HTML documentation
cd docs && make html
```

## Common Tasks

### Adding a New Dependency

```bash
# Add runtime dependency
poetry add package-name

# Add development dependency
poetry add --group dev package-name

# Update dependencies
poetry update
```

### Creating a New Module

1. Create the module file in `src/cow_performance/`
2. Add `__init__.py` if it's a package
3. Write tests in `tests/unit/` or `tests/integration/`
4. Add type hints
5. Write docstrings
6. Run tests and linting

### Releasing a New Version

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a git tag: `git tag v0.2.0`
4. Push tag: `git push origin v0.2.0`
5. GitHub Actions will handle the release

## Troubleshooting

### Poetry Issues

```bash
# Clear cache
poetry cache clear pypi --all

# Reinstall dependencies
rm -rf .venv poetry.lock
poetry install
```

### Test Failures

1. Run tests verbosely: `pytest -vv`
2. Run specific failing test: `pytest path/to/test.py::test_name -vv`
3. Check for outdated fixtures or mocks
4. Verify test environment matches CI

### Type Checking Errors

1. Review mypy error message carefully
2. Add type hints to untyped code
3. Use `# type: ignore` as a last resort with a comment explaining why
4. Check if external library has type stubs available

## Resources

- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Pytest Documentation](https://docs.pytest.org/)
- [Black Documentation](https://black.readthedocs.io/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Async/Await](https://realpython.com/async-io-python/)

## Getting Help

- Check existing issues on GitHub
- Ask in project discussions
- Review architecture and development docs
- Reach out to maintainers

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed contribution guidelines.
