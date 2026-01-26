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
  - Order generation components
  - Token pairs, validation, factory, templates

- **Integration tests** (`tests/integration/`): Test component interactions
  - End-to-end order generation
  - Bulk generation (100+ orders)
  - Serialization/deserialization
  - Multi-network support
  - Performance benchmarks

- **End-to-end tests** (`tests/e2e/`): Test complete workflows with live services (requires docker-compose environment)
  - Full order lifecycle
  - Conditional orders (TWAP, Stop-Loss) with ComposableCow
  - Hooks orders (pre-hooks and post-hooks)
  - Safe wallet deployment and approvals
  - EIP-1271 signature validation

## End-to-End Tests

This section provides comprehensive guidance for running end-to-end tests that interact with a real CoW Protocol environment running in docker-compose.

### E2E Prerequisites

1. **Docker and Docker Compose** installed
2. **Ethereum RPC endpoint** (Alchemy, Infura, etc.)
3. **Running docker-compose environment**

### E2E Setup

#### 1. Configure Environment

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and set your Ethereum RPC URL:

```bash
ETH_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY
```

#### 2. Start Docker Environment

Start all services:

```bash
docker compose up -d
```

Or with monitoring (Prometheus & Grafana):

```bash
docker compose --profile monitoring up -d
```

#### 3. Wait for Services

Wait for all services to be healthy (this can take 2-3 minutes):

```bash
# Check service status
docker compose ps

# Watch logs
docker compose logs -f

# Wait for orderbook to be ready
curl http://localhost:8080/api/v1/version
```

The services are ready when:
- ✅ Anvil (chain) is running on port 8545
- ✅ Orderbook API is responding on port 8080
- ✅ Autopilot, Driver, and Solver are running

### Running E2E Tests

#### Run All E2E Tests

```bash
pytest tests/e2e/ -v -m e2e
```

#### Run Specific Test

```bash
# Test WETH→DAI market order settlement
pytest tests/e2e/test_order_settlement.py::TestOrderSettlement::test_market_order_weth_to_dai_settlement -v

# Test DAI→WETH market order settlement
pytest tests/e2e/test_order_settlement.py::TestOrderSettlement::test_market_order_dai_to_weth_settlement -v

# Test limit order
pytest tests/e2e/test_order_settlement.py::TestOrderSettlement::test_limit_order_settlement -v

# Test multiple concurrent orders
pytest tests/e2e/test_order_settlement.py::TestOrderSettlement::test_multiple_orders_concurrent_settlement -v
```

#### Run with Verbose Output

```bash
pytest tests/e2e/ -v -s -m e2e
```

The `-s` flag shows print statements, which is useful for watching settlement progress.

### What the E2E Tests Do

#### 1. Order Settlement Tests

The e2e tests perform real order submission and settlement:

1. **Fund Test Accounts**
   - Creates new Ethereum accounts
   - Funds them with ETH for gas
   - Funds them with tokens (WETH, DAI, etc.) by impersonating whale addresses
   - Approves settlement contract to spend tokens

2. **Submit Orders**
   - Generates orders using OrderFactory
   - Signs orders with EIP-712
   - Submits to orderbook API at http://localhost:8080

3. **Wait for Settlement**
   - Polls orderbook API every 5 seconds
   - Checks for trades
   - Verifies order status (fulfilled, expired, etc.)
   - Timeout after 60-120 seconds

4. **Verify Results**
   - Checks token balances changed as expected
   - Verifies trades occurred
   - Confirms settlement on-chain

#### 2. Test Coverage

Current e2e tests cover:

- ✅ **Market Orders**: WETH→DAI and DAI→WETH
- ✅ **Limit Orders**: With better-than-market pricing
- ✅ **Multiple Orders**: Concurrent submission and settlement
- ⏳ **Full User Simulation**: With TraderOrchestrator (TODO)

#### 3. Conditional Orders

Conditional orders (TWAP, Stop-Loss, Good-After-Time) require the watch-tower service and additional setup. These will be added in future iterations.

### E2E Troubleshooting

#### Services Not Ready

If tests fail with connection errors:

```bash
# Check all services are running
docker compose ps

# Check orderbook logs
docker compose logs orderbook

# Restart services
docker compose restart
```

#### Orders Not Settling

If orders submit but don't settle:

1. **Check Autopilot logs**: `docker compose logs autopilot`
2. **Check Solver logs**: `docker compose logs baseline`
3. **Check Driver logs**: `docker compose logs driver`
4. **Verify Anvil is producing blocks**: `docker compose logs chain`

Common issues:
- Autopilot not running auctions (check SETTLE_INTERVAL)
- Solver not finding solutions (check liquidity on UniswapV2)
- Gas price issues (check Anvil configuration)

#### Token Funding Fails

If whale impersonation fails:

1. Check whale addresses have tokens on the forked block
2. Verify Anvil fork is at recent block
3. Check RPC endpoint is working

#### "Anvil not connected"

If Web3 can't connect to Anvil:

```bash
# Check Anvil is running
docker compose ps chain

# Check Anvil logs
docker compose logs chain

# Try restarting
docker compose restart chain
```

### E2E Test Markers

E2E tests use pytest markers:

- `@pytest.mark.e2e` - Marks as end-to-end test
- `@pytest.mark.skip` - Skips test (for long-running or incomplete tests)

Run only e2e tests:
```bash
pytest -m e2e
```

### E2E Environment Variables

You can customize endpoints:

```bash
# Anvil RPC URL (default: http://localhost:8545)
export ANVIL_RPC_URL=http://localhost:8545

# Orderbook API URL (default: http://localhost:8080)
export ORDERBOOK_API_URL=http://localhost:8080

# Run tests
pytest tests/e2e/ -m e2e
```

### E2E CI/CD Integration

For CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Start docker-compose
  run: |
    docker compose up -d
    sleep 60  # Wait for services to be ready

- name: Run e2e tests
  run: |
    pytest tests/e2e/ -m e2e -v

- name: Stop docker-compose
  run: docker compose down
```

### E2E Next Steps

To add more e2e tests:

1. **Conditional Orders**: Test TWAP, Stop-Loss, Good-After-Time orders
2. **Full Simulation**: Test TraderOrchestrator with multiple concurrent traders
3. **Performance Tests**: Measure settlement times, throughput, etc.
4. **Failure Scenarios**: Test order cancellation, expiry, etc.
5. **Safe Wallets**: Test EIP-1271 signatures with Safe wallets

### E2E Resources

- [CoW Protocol Documentation](https://docs.cow.fi/)
- [Orderbook API Reference](https://api.cow.fi/docs/)
- [Anvil Documentation](https://book.getfoundry.sh/anvil/)

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
- ✅ **High Performance**: Fast order generation rate
- ✅ **Type Safe**: Full type hints and Pydantic validation
- ✅ **Well Tested**: Comprehensive unit and integration test coverage

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

## User Simulation Module

The user simulation module provides comprehensive tools for simulating realistic trading behavior with multiple concurrent users, Safe wallet integration, and advanced order types including hooks.

### Quick Start

```python
from cow_performance.load_generation import (
    TraderPool,
    SafeWallet,
    submit_conditional_order,
    OrderSigner,
)
from web3 import Web3

# Connect to forked network
web3 = Web3(Web3.HTTPProvider("http://localhost:8545"))

# Create a pool of traders
trader_pool = TraderPool(num_traders=10)

# Get a trader
trader = trader_pool.get_random_trader()
print(f"Trader address: {trader.address}")
print(f"Orders submitted: {trader.orders_submitted}")

# Deploy Safe wallet for conditional orders
safe_wallet = SafeWallet.deploy(
    web3=web3,
    owner=trader.get_account(),
    chain_id=1
)
print(f"Safe wallet deployed at: {safe_wallet.address}")

# Attach Safe to trader
trader.safe_wallet = safe_wallet
```

### Components

#### Trader Account Management

**TraderAccount** - Individual trader with private key and metadata:

```python
from cow_performance.load_generation import TraderAccount

# Generate new trader
trader = TraderAccount.generate()

# From existing private key
trader = TraderAccount.from_private_key("0x...")

# Access trader info
print(f"Address: {trader.address}")
print(f"Nonce: {trader.nonce}")
print(f"Orders submitted: {trader.orders_submitted}")

# Get LocalAccount for signing
account = trader.get_account()

# Check Safe wallet integration
if trader.has_safe_wallet():
    safe_address = trader.get_safe_address()
    trading_address = trader.get_trading_address()  # Returns Safe or EOA
```

**TraderPool** - Manage multiple traders for concurrent simulations:

```python
from cow_performance.load_generation import TraderPool

# Create pool of traders
pool = TraderPool(num_traders=20)

# Access traders
trader1 = pool.get_trader(0)              # By index
random_trader = pool.get_random_trader()  # Random selection
next_trader = pool.get_next_trader()      # Round-robin

# Pool statistics
pool_size = pool.get_pool_size()
total_orders = pool.get_total_orders_submitted()
all_traders = pool.get_all_traders()
```

#### Safe Wallet Integration

**SafeWallet** - Gnosis Safe deployment and management for EIP-1271 signatures:

```python
from cow_performance.load_generation import SafeWallet, deploy_safe_wallet
from web3 import Web3

web3 = Web3(Web3.HTTPProvider("http://localhost:8545"))
trader_account = trader.get_account()

# Deploy Safe wallet
safe_wallet = SafeWallet.deploy(
    web3=web3,
    owner=trader_account,
    chain_id=1
)

# Or use convenience function
safe_wallet = deploy_safe_wallet(web3, trader_account)

# Safe operations
nonce = safe_wallet.get_nonce()

# Execute transactions through Safe
tx_hash = safe_wallet.exec_transaction(
    to="0x...",
    value=0,
    data=b"...",
    operation=0  # 0=CALL, 1=DELEGATECALL
)

# Approve tokens for trading
safe_wallet.approve_token(
    token_address="0x...",
    spender="0x...",
    amount=1000 * 10**18
)

# Sign messages (EIP-1271)
signature = safe_wallet.sign_message(message_hash)
```

#### Order Signing

**OrderSigner** - EIP-712 signatures for EOAs:

```python
from cow_performance.load_generation import OrderSigner, OrderParameters

signer = OrderSigner(
    chain_id=1,
    settlement_contract="0x9008D19f58AAbD9eD0D60971565AA8510560ab41"
)

# Sign order with EOA
signed_order = signer.sign_order(order_params, trader.get_account())
```

**ConditionalOrderSigner** - EIP-1271 signatures for Safe wallets:

```python
from cow_performance.load_generation import ConditionalOrderSigner

signer = ConditionalOrderSigner(
    safe_wallet=safe_wallet,
    composable_cow_address="0xfdaFc9d1902f4e0b84f65F49f244b32b31013b74"
)

# Create EIP-1271 signature for conditional order
signature = signer.create_signature(order_params)
```

#### ComposableCow Submission

Submit conditional orders (TWAP, Stop-Loss) to the blockchain:

```python
from cow_performance.load_generation import (
    submit_conditional_order,
    get_tradeable_order,
    remove_conditional_order,
    ConditionalOrderFactory,
)

# Create conditional order
factory = ConditionalOrderFactory(
    token_pair_registry=token_registry,
    chain_id=1,
    safe_wallet_address=safe_wallet.address,
)

twap_order = factory.create_twap_order(
    total_amount=1000.0,
    num_parts=5,
    interval_seconds=300,
)

# Submit to ComposableCow contract
tx_hash = submit_conditional_order(
    web3=web3,
    composable_cow_address="0xfdaFc9d1902f4e0b84f65F49f244b32b31013b74",
    safe_wallet=safe_wallet,
    conditional_order=twap_order,
    dispatch=True,  # Immediately dispatch to watchtower
)

print(f"Conditional order submitted: {tx_hash.hex()}")

# Check if order is tradeable
tradeable = get_tradeable_order(
    web3=web3,
    composable_cow_address="0xfdaFc9d1902f4e0b84f65F49f244b32b31013b74",
    owner=safe_wallet.address,
    conditional_order_params={
        "handler": twap_order.params.handler,
        "salt": twap_order.params.salt,
        "staticInput": twap_order.params.staticInput,
    },
)

if tradeable:
    order, signature = tradeable
    print("Order is tradeable!")

# Remove conditional order
remove_conditional_order(
    web3=web3,
    composable_cow_address="0xfdaFc9d1902f4e0b84f65F49f244b32b31013b74",
    safe_wallet=safe_wallet,
    conditional_order_params={...},
)
```

#### Hooks Orders

Create orders with custom pre-hooks and post-hooks that execute atomically with settlement:

```python
import json
from web3 import Web3
from cow_performance.load_generation import OrderParameters, OrderSigner

# Create hooks metadata
hooks_metadata = {
    "version": "0.9.0",
    "appCode": "CoW Swap",
    "hooks": {
        "version": "0.1.0",
        "pre": [
            {
                "target": "0x...",      # Contract to call
                "callData": "0x...",    # Encoded function call
                "gasLimit": 100000,     # Gas limit for hook
            }
        ],
        "post": [
            {
                "target": "0x...",
                "callData": "0x...",
                "gasLimit": 100000,
            }
        ],
    },
}

# Generate appData hash
app_data_json = json.dumps(hooks_metadata)
app_data_hash = Web3.keccak(text=app_data_json).hex()

# Upload appData to orderbook (required before order submission)
import requests
response = requests.put(
    f"http://localhost:8080/api/v1/app_data/{app_data_hash[2:]}",
    json={"fullAppData": app_data_json},
)

# Create order with hooks
order_params = OrderParameters(
    sellToken="0x...",
    buyToken="0x...",
    sellAmount="1000000000000000000",
    buyAmount="1000000000000000000",
    validTo=1234567890,
    appData=app_data_hash,  # Include hooks via appData
    feeAmount="0",
    kind="sell",
    partiallyFillable=False,
)

# Sign and submit
signer = OrderSigner(chain_id=1, settlement_contract="0x...")
signed_order = signer.sign_order(order_params, trader.get_account())

# Submit to orderbook
response = requests.post(
    "http://localhost:8080/api/v1/orders",
    json=signed_order.model_dump(by_alias=True),
)
```

**Common Hook Use Cases:**

- **Pre-hooks**: Permit signatures (gasless approvals), state checks, price validations
- **Post-hooks**: Token transfers, staking, LP deposits, reward claiming

#### Trader Simulation & Orchestration

Simulate realistic trading behavior with configurable patterns:

```python
from cow_performance.load_generation import (
    TraderSimulator,
    TraderOrchestrator,
    OrchestrationConfig,
    TraderBehaviorConfig,
    TradingPattern,
)

# Configure trader behavior
behavior_config = TraderBehaviorConfig(
    think_time_range=(1.0, 5.0),           # Think time between actions (seconds)
    orders_per_session_range=(5, 20),      # Orders per trading session
    trading_pattern=TradingPattern.BURST,   # CONSTANT, BURST, or RAMP_UP
)

# Create simulator for a trader
simulator = TraderSimulator(
    trader_account=trader,
    order_factory=order_factory,
    behavior_config=behavior_config,
)

# Run simulation
await simulator.simulate_trading_session()

# Orchestrate multiple traders
orchestration_config = OrchestrationConfig(
    num_traders=10,
    orders_per_trader=100,
    duration_seconds=600,
    ramp_up_seconds=60,
)

orchestrator = TraderOrchestrator(
    trader_pool=trader_pool,
    order_factory=order_factory,
    config=orchestration_config,
)

# Run load test
metrics = await orchestrator.run_load_test()
print(f"Total orders submitted: {metrics.total_orders}")
print(f"Orders per second: {metrics.orders_per_second}")
```

### Order Tracking

Track order lifecycle and performance metrics:

```python
from cow_performance.load_generation import OrderTracker, OrderStatus

tracker = OrderTracker()

# Track order submission
tracker.track_submission(order_uid, order_data)

# Update order status
tracker.update_status(order_uid, OrderStatus.FULFILLED)

# Get metrics
metrics = tracker.get_metrics()
print(f"Success rate: {metrics.success_rate * 100}%")
print(f"Average latency: {metrics.average_latency}s")

# Get order history
history = tracker.get_order_history(order_uid)
```

### End-to-End Testing

Complete e2e tests demonstrating full workflows:

```bash
# Run e2e tests (requires docker-compose environment)
pytest tests/e2e/ -v

# Test regular order submission
pytest tests/e2e/test_order_settlement.py -v

# Test conditional orders (TWAP, Stop-Loss)
pytest tests/e2e/test_conditional_orders.py -v

# Test hooks orders
pytest tests/e2e/test_hooks_orders.py -v
```

**Example test scenarios covered:**

- ✅ Market order submission and settlement
- ✅ TWAP order creation and ComposableCow submission
- ✅ Stop-Loss order creation with oracle integration
- ✅ Pre-hook orders (execute before swap)
- ✅ Post-hook orders (execute after swap)
- ✅ Safe wallet deployment and token approvals
- ✅ EIP-1271 signature validation

### Features

- ✅ **Multi-Trader Simulation**: Concurrent trading with configurable pools
- ✅ **Safe Wallet Support**: Full Gnosis Safe integration for advanced orders
- ✅ **EIP-1271 Signatures**: Smart contract signature validation
- ✅ **Conditional Orders**: On-chain TWAP, Stop-Loss via ComposableCow
- ✅ **Hooks Integration**: Pre/post-settlement custom calls
- ✅ **Order Tracking**: Lifecycle monitoring and metrics collection
- ✅ **Realistic Behavior**: Configurable trading patterns and timing
- ✅ **Type Safe**: Full type hints and validation
- ✅ **Well Tested**: Comprehensive e2e test coverage

### Architecture

```
User Simulation Module
│
├── Trader Management
│   ├── TraderAccount (EOA generation and management)
│   └── TraderPool (Multi-trader coordination)
│
├── Safe Wallet Layer
│   ├── SafeWallet (Deployment and management)
│   └── EIP-1271 signature generation
│
├── Order Creation
│   ├── OrderFactory (Regular orders)
│   ├── ConditionalOrderFactory (TWAP, Stop-Loss)
│   └── Hooks metadata generation
│
├── Order Signing
│   ├── OrderSigner (EIP-712 for EOAs)
│   └── ConditionalOrderSigner (EIP-1271 for Safe)
│
├── Order Submission
│   ├── Orderbook API submission (regular orders)
│   ├── ComposableCow submission (conditional orders)
│   └── AppData upload (hooks orders)
│
└── Simulation & Orchestration
    ├── TraderSimulator (Individual trader behavior)
    ├── TraderOrchestrator (Multi-trader coordination)
    └── OrderTracker (Metrics and monitoring)
```

### Technical Requirements

**For Regular Orders:**
- EOA with ETH for gas
- Token approvals to VaultRelayer

**For Conditional Orders:**
- Safe wallet deployment
- Safe funded with ETH for gas
- Token approvals from Safe to VaultRelayer
- ComposableCow contract access

**For Hooks Orders:**
- AppData document upload to orderbook
- HooksTrampoline contract deployed
- Token approvals for trading

### Additional Resources

- [Hooks Implementation Guide](docs/hooks-implementation.md)
- [Safe Wallet Documentation](https://docs.safe.global/)
- [ComposableCow Documentation](https://docs.cow.fi/cow-protocol/reference/contracts/periphery/composable-cow)
- [CoW Protocol Hooks](https://docs.cow.fi/cow-protocol/reference/core/intents/hooks)

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

### Milestone 1: Load Generation Framework (Near Complete)
- [x] Project setup and repository structure
- [x] Fork mode environment setup
- [x] Order generation engine
- [x] User simulation module
  - [x] TraderAccount and TraderPool
  - [x] Safe wallet deployment and integration
  - [x] Order signing (EIP-712 and EIP-1271)
  - [x] ComposableCow submission for conditional orders
  - [x] Hooks orders (pre-hooks and post-hooks)
  - [x] Trader simulation and orchestration
  - [x] Order tracking and metrics
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
