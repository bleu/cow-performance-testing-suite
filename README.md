# CoW Performance Testing Suite

Comprehensive performance testing suite for the CoW Protocol Playground, enabling load testing, benchmarking, and regression detection using Anvil fork mode.

## Features

- 🚀 **Load Generation**: Simulate realistic trading patterns with configurable strategies
- 📊 **Performance Benchmarking**: Measure order lifecycle, API performance, and resource utilization
- 📈 **Metrics & Visualization**: Prometheus exporters and Grafana dashboards
- 🔍 **Regression Detection**: Statistical comparison against baselines
- 🐳 **Fork Mode Testing**: Test against mainnet state using Anvil fork mode
- 🎯 **Scenario Library**: Predefined scenarios from light to heavy loads
- 🔧 **Flexible Configuration**: YAML-based scenarios with inheritance and composition

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Poetry (for dependency management)
- Docker and Docker Compose (for fork mode environment)
- Access to an Ethereum archive node (for fork mode)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/cowprotocol/cow-performance-testing-suite.git
   cd cow-performance-testing-suite
   ```

2. **Install dependencies with Poetry:**
   ```bash
   poetry install
   ```

3. **Activate the virtual environment:**
   ```bash
   poetry shell
   ```

4. **Verify installation:**
   ```bash
   cow-perf --version
   ```

### Your First Performance Test

```bash
# Run a light load scenario
cow-perf run --scenario light-load

# View available scenarios
cow-perf scenarios list

# Get help
cow-perf --help
```

## Fork Mode Environment Setup

The CoW Performance Testing Suite uses **Anvil fork mode** to create a realistic testing environment by forking mainnet state. This allows you to test against real liquidity, contracts, and state without spending real gas or affecting mainnet.

### Prerequisites

- Docker and Docker Compose installed
- Access to an Ethereum RPC endpoint (Alchemy, Infura, or similar)
- At least 8GB RAM available for Docker

### Initial Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/bleu/cow-performance-testing-suite.git
   cd cow-performance-testing-suite
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set your Ethereum RPC URL:
   ```bash
   ETH_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY
   ```

3. **Start the fork mode environment:**
   ```bash
   # Start core services
   docker compose up -d

   # Or start with monitoring (Prometheus & Grafana)
   docker compose --profile monitoring up -d
   ```

   **Note**: First startup will download Docker images from GitHub Container Registry (ghcr.io).

4. **Wait for services to be ready:**
   ```bash
   # Check services are running
   docker compose ps

   # Follow logs
   docker compose logs -f
   ```

### Manual Setup (Alternative)

If you prefer to start services manually:

```bash
# Start core services only
docker compose up -d

# Start with monitoring (Prometheus & Grafana)
docker compose --profile monitoring up -d

# View logs
docker compose logs -f

# Check service status
docker compose ps

# Stop services
docker compose down
```

### Service URLs

Once the environment is running, the following services are available:

| Service | URL | Description |
|---------|-----|-------------|
| Anvil RPC | http://localhost:8545 | Forked Ethereum node |
| Orderbook API | http://localhost:8080 | CoW Protocol orderbook |
| Driver | http://localhost:9000 | Driver service |
| Baseline Solver | http://localhost:9001 | AMM-based solver |
| PostgreSQL | localhost:5432 | Database |
| Prometheus | http://localhost:9090 | Metrics (with monitoring profile) |
| Grafana | http://localhost:3000 | Dashboards (with monitoring profile) |

### Verifying the Environment

```bash
# Check if Anvil is running
cast block-number --rpc-url http://localhost:8545

# Check orderbook API
curl http://localhost:8080/api/v1/version

# Check all services status
docker compose ps

# Check database
docker exec $(docker ps -qf "name=db") pg_isready -U postgres
```

### Troubleshooting

#### Services failing to start

```bash
# Check logs
docker compose logs orderbook
docker compose logs autopilot
docker compose logs driver

# Restart a specific service
docker compose restart orderbook

# Rebuild and restart
docker compose up -d --build orderbook
```

#### Database connection issues

```bash
# Check database is running
docker compose ps db

# Check database logs
docker compose logs db

# Reset database
docker compose down -v
docker compose up -d
```

#### Anvil fork issues

Make sure your `ETH_RPC_URL` in `.env` is:
- A valid Ethereum mainnet RPC URL
- Has sufficient rate limits
- Supports `eth_blockNumber` and archive state queries

#### Out of memory

Increase Docker memory limit to at least 8GB:
- Docker Desktop → Settings → Resources → Memory

### Environment Management

```bash
# Stop all services
docker compose down

# Stop and remove volumes (fresh start)
docker compose down -v

# View resource usage
docker stats

# Clean up old images and containers
docker system prune -a
```

## Development Setup

### Setting up the development environment

1. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Install development dependencies:**
   ```bash
   poetry install --with dev
   ```

3. **Install pre-commit hooks:**
   ```bash
   poetry run pre-commit install
   ```

4. **Run tests:**
   ```bash
   poetry run pytest
   ```

### Code Quality

We use the following tools to maintain code quality:

- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking
- **Pytest** for testing

Run all checks:
```bash
# Format code
poetry run black src/ tests/

# Lint
poetry run ruff check src/ tests/

# Type check
poetry run mypy src/

# Run tests
poetry run pytest
```

## Project Structure

```
cow-performance-testing-suite/
├── src/cow_performance/      # Main package
│   ├── cli/                  # CLI interface
│   ├── load_generation/      # Order generation and submission strategies
│   ├── benchmarking/         # Performance measurement and comparison
│   ├── metrics/              # Metrics collection and export
│   └── scenarios/            # Test scenario management
├── tests/                    # Test suite
│   ├── unit/                 # Unit tests
│   └── integration/          # Integration tests
├── docs/                     # Documentation
├── configs/scenarios/        # Scenario configurations
├── docker/                   # Docker configurations
└── scripts/                  # Helper scripts
```

## Usage Examples

### Running Scenarios

```bash
# Run predefined scenarios
cow-perf run --scenario light-load
cow-perf run --scenario medium-load --duration 600

# Run custom scenario
cow-perf run --scenario ./my-scenario.yml
```

### Baseline Management

```bash
# Create a baseline
cow-perf baselines save my-baseline

# List baselines
cow-perf baselines list

# Compare against baseline
cow-perf run --scenario medium-load --baseline my-baseline
```

### Configuration

```bash
# Show current configuration
cow-perf config show

# Initialize new scenario
cow-perf config init
```

## Testing

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run unit tests only
poetry run pytest tests/unit -v

# Run integration tests
poetry run pytest tests/integration -v

# Run with coverage
poetry run pytest --cov=src/cow_performance --cov-report=html

# Run specific test markers
poetry run pytest -m integration
poetry run pytest -m "integration and not slow"
```

### Using Virtual Environment

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install project in development mode
pip install -e .

# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock

# Run tests
pytest tests/integration/ -v
```

### Test Organization

- **Unit tests** (`tests/unit/`): Test individual components in isolation
  - 58 tests covering all order generation components
  - Token pairs, validation, factory, templates

- **Integration tests** (`tests/integration/`): Test component interactions
  - 12 tests validating end-to-end order generation
  - Bulk generation (100+ orders)
  - Serialization/deserialization
  - Multi-network support
  - Performance benchmarks (1000 orders)

- **End-to-end tests**: Test complete workflows (coming in M5)

### Test Results

Current test coverage:
- **Unit Tests**: 58/58 passing ✅
- **Integration Tests**: 12/12 passing ✅
- **Code Coverage**: 72%
- **Performance**: 370+ orders/sec

## Docker Usage

### Build the Docker image

```bash
docker build -t cow-performance-testing-suite -f docker/Dockerfile .
```

### Run in Docker

```bash
# Show help
docker run cow-performance-testing-suite --help

# Run a scenario
docker run -v $(pwd)/configs:/app/configs \
  cow-performance-testing-suite run --scenario light-load
```

## Order Generation Module

The order generation module provides comprehensive capabilities for creating realistic CoW Protocol orders for performance testing.

### Quick Start

```python
from eth_account import Account
from cow_performance.load_generation import (
    OrderFactory,
    create_mainnet_token_registry,
)

# Create token registry and factory
token_registry = create_mainnet_token_registry()
factory = OrderFactory(
    token_pair_registry=token_registry,
    chain_id=1,
    settlement_contract="0x9008D19f58AAbD9eD0D60971565AA8510560ab41",
)

# Create trader and generate orders
trader = Account.create()
market_order = factory.create_market_order(trader)
limit_order = factory.create_limit_order(trader, limit_price=0.99)
batch_orders = factory.create_batch_orders(trader, count=100)
```

### Components

#### Order Schema
Pydantic models matching CoW Protocol specifications:
- `OrderKind` (buy/sell), `OrderBalance`, `SigningScheme` enums
- `OrderParameters` - Core order parameters with validation
- `SignedOrder` - Complete order with EIP-712 signature
- Full EIP-712 domain and type definitions

#### Token Pair Management
- `Token` - Token metadata (address, symbol, decimals)
- `TokenPair` - Trading pairs with selection weights
- `TokenPairRegistry` - Multiple selection strategies:
  - Random selection
  - Weighted random (realistic distributions)
  - Sequential (round-robin)
- Pre-configured registries for Ethereum mainnet and Polygon

#### Order Factory
Generate orders with realistic parameters:
- `create_market_order()` - Market orders at current price
- `create_limit_order()` - Limit orders with custom price
- `create_batch_orders()` - Bulk order generation
- Configurable amounts, fees, validity periods
- Log-scale amount distribution for realism

#### Order Templates
Pre-configured templates for common scenarios:
- Small/medium/large market orders
- Conservative/aggressive limit orders
- WETH buy orders
- Stablecoin swaps
- Partially fillable orders

```python
from cow_performance.load_generation import create_default_templates

template_registry = create_default_templates()
order = template_registry.create_order_from_template(
    template_name="small_market",
    factory=factory,
    trader_account=trader,
)
```

#### Order Validation
Comprehensive validation utilities:
```python
from cow_performance.load_generation import validate_order_parameters

errors = validate_order_parameters(order_params)
if errors:
    print("Validation errors:", errors)
```

### Features

- ✅ **CoW Protocol Compatible**: Orders validated against real orderbook API
- ✅ **EIP-712 Signatures**: Cryptographically signed with proper domain separation
- ✅ **Multi-Network**: Supports Ethereum mainnet and Polygon
- ✅ **Realistic Parameters**: Log-scale amounts, weighted token pair selection
- ✅ **High Performance**: 370+ orders/sec generation rate
- ✅ **Type Safe**: Full type hints and Pydantic validation
- ✅ **Well Tested**: 70 unit + integration tests, 72% coverage

### Integration with CoW Protocol

Orders can be submitted directly to the orderbook API:

```python
import aiohttp

async def submit_order(order: SignedOrder):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8080/api/v1/orders",
            json=order.model_dump(by_alias=True),
        ) as response:
            return await response.json()
```

## Conditional Orders (Advanced)

The order generation module now supports advanced CoW Protocol conditional orders through ComposableCow, enabling TWAP, Stop-Loss, and Good-After-Time orders for sophisticated trading strategies.

### Quick Start

```python
from cow_performance.load_generation import (
    ConditionalOrderFactory,
    create_mainnet_token_registry,
)

# Create conditional order factory
token_registry = create_mainnet_token_registry()
factory = ConditionalOrderFactory(
    token_pair_registry=token_registry,
    chain_id=1,
    safe_wallet_address="0x...",  # Your Safe wallet address
)

# Create TWAP order: 3000 USDC split into 3 parts over 12 minutes
twap_order = factory.create_twap_order(
    total_amount=3000.0,
    num_parts=3,
    interval_seconds=240,  # 4 minutes between parts
)

# Create stop-loss: Sell 1 WETH when price drops 10%
stop_loss_order = factory.create_stop_loss_order(
    sell_amount=1.0,
    strike_percentage=90.0,  # Trigger at 90% of current price
    valid_duration=3600,     # Valid for 1 hour
)

# Create good-after-time: Order activates after 5 minutes
delayed_order = factory.create_good_after_time_order(
    sell_amount=10.0,
    delay_seconds=300,
    valid_duration=3600,
)

# Generate mixed batch of conditional orders
batch = factory.create_batch_conditional_orders(
    count=50,
    order_types=["twap", "stop_loss", "good_after_time"]
)
```

### Conditional Order Types

#### TWAP Orders

Time-Weighted Average Price orders split large trades into smaller parts executed over time to minimize market impact:

```python
twap = factory.create_twap_order(
    total_amount=1000.0,      # Total amount to trade
    num_parts=5,              # Split into 5 parts
    interval_seconds=600,     # 10 minutes between parts
    start_delay_seconds=10,   # Start after 10 seconds
)
```

**Use cases:**
- Large trades that would move the market
- Gradual position entry/exit
- Time-based trading strategies

#### Stop-Loss Orders

Price-triggered orders using Chainlink oracles:

```python
stop_loss = factory.create_stop_loss_order(
    sell_amount=10.0,
    strike_percentage=85.0,   # Trigger when price drops to 85%
    valid_duration=14400,     # Valid for 4 hours
)
```

**Use cases:**
- Risk management and downside protection
- Automated liquidation strategies
- Price-based portfolio rebalancing

#### Good-After-Time Orders

Orders that activate after a specified delay:

```python
delayed = factory.create_good_after_time_order(
    sell_amount=5.0,
    delay_seconds=1800,       # Activate after 30 minutes
    valid_duration=7200,      # Then valid for 2 hours
)
```

**Use cases:**
- Scheduled trades
- Post-event trading strategies
- Time-based DCA (Dollar Cost Averaging)

### Conditional Order Templates

Pre-configured templates for common conditional order patterns:

```python
from cow_performance.load_generation import (
    create_default_conditional_templates,
    ConditionalOrderTemplateRegistry,
)

# Load templates
templates = create_default_conditional_templates()
registry = ConditionalOrderTemplateRegistry(templates)

# Available TWAP templates
twap_small = registry.get_template("twap_small")        # 3 parts, 4 min intervals
twap_medium = registry.get_template("twap_medium")      # 5 parts, 5 min intervals
twap_large = registry.get_template("twap_large")        # 10 parts, 10 min intervals

# Available Stop-Loss templates
sl_conservative = registry.get_template("stop_loss_conservative")  # 5% drop
sl_moderate = registry.get_template("stop_loss_moderate")          # 10% drop
sl_aggressive = registry.get_template("stop_loss_aggressive")      # 20% drop

# Available Good-After-Time templates
delayed_short = registry.get_template("delayed_order_short")   # 5 min delay
delayed_medium = registry.get_template("delayed_order_medium") # 30 min delay
delayed_long = registry.get_template("delayed_order_long")     # 1 hour delay

# Use template to generate order
order = factory.create_twap_order(
    num_parts=twap_medium.num_parts,
    interval_seconds=twap_medium.interval_seconds,
)
```

### Handler and Oracle Registries

The module includes comprehensive registries for ComposableCow handlers and Chainlink oracles:

```python
from cow_performance.load_generation import (
    get_handler_address,
    get_composable_cow_address,
    OracleRegistry,
)

# Get handler addresses
twap_handler = get_handler_address("twap", chain_id=1)
stop_loss_handler = get_handler_address("stop_loss", chain_id=1)

# Get ComposableCow address
composable_cow = get_composable_cow_address(chain_id=1)

# Work with oracles
oracle_registry = OracleRegistry(chain_id=1)
weth_oracle = oracle_registry.get_oracle_for_token("WETH")
usdc_oracle = oracle_registry.get_oracle_for_token("USDC")

# List available tokens with oracles
available_tokens = oracle_registry.get_available_tokens()
print(f"Tokens with oracles: {available_tokens}")
```

### Network Support

Conditional orders are currently configured for Ethereum Mainnet:

```python
# Ethereum Mainnet
factory = ConditionalOrderFactory(
    token_pair_registry=token_registry,
    chain_id=1,
    safe_wallet_address="0x...",
)
```

The architecture is designed to be expandable to additional networks in the future by adding handler and oracle addresses to the respective registries.

### Features

- ✅ **TWAP Orders**: Split large trades over time
- ✅ **Stop-Loss Orders**: Oracle-triggered protective orders
- ✅ **Good-After-Time Orders**: Time-delayed execution
- ✅ **Template System**: Pre-configured order patterns
- ✅ **Mainnet Support**: Ethereum mainnet (expandable to other networks)
- ✅ **Oracle Integration**: Chainlink price feeds for 8 major tokens
- ✅ **Handler Registry**: Automatic handler address resolution
- ✅ **Type Safe**: Full Pydantic validation and type hints
- ✅ **Well Tested**: Comprehensive unit and integration tests

### Technical Details

Conditional orders use the ComposableCow framework and require:
- Safe wallet (EIP-1271 signatures)
- ComposableCow deployment on target network
- Handler contracts for each order type
- Chainlink oracles for stop-loss orders

Orders are encoded using ABI encoding and submitted to ComposableCow for conditional execution by the CoW Protocol watchtower service.

## Documentation

- [Architecture](docs/architecture.md) - System design and architecture overview
- [Development Guide](docs/development.md) - Development setup and guidelines
- [Configuration Reference](docs/configuration.md) - Configuration options (coming soon)
- [Metrics Guide](docs/metrics.md) - Understanding metrics (coming soon)

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## Roadmap

### Milestone 1: Load Generation Framework (In Progress)
- [x] Project setup and repository structure
- [x] Fork mode environment setup
- [x] Order generation engine
- [ ] User simulation module
- [ ] CLI tool interface
- [ ] Order submission strategies

### Milestone 2: Performance Benchmarking (Next)
- [ ] Metrics collection framework
- [ ] Baseline snapshot system
- [ ] Comparison engine and regression detection
- [ ] Automated reporting

### Milestone 3: Metrics & Visualization
- [ ] Prometheus exporters
- [ ] Grafana dashboards
- [ ] Alerting rules

### Milestone 4: Test Scenarios
- [ ] Predefined test scenarios library
- [ ] Scenario configuration system
- [ ] Example scenarios collection

### Milestone 5: Final Validation & Documentation
- [ ] End-to-end validation
- [ ] Comprehensive documentation
- [ ] Offline mode exploration (stretch goal)

## License

MIT License - see [LICENSE](LICENSE) for details

## Support

- **Issues**: [GitHub Issues](https://github.com/cowprotocol/cow-performance-testing-suite/issues)
- **Discussions**: [GitHub Discussions](https://github.com/cowprotocol/cow-performance-testing-suite/discussions)
- **Documentation**: [docs/](docs/)

## Acknowledgments

Built with ❤️ by the CoW Protocol team for comprehensive performance testing of the CoW Protocol Playground.
