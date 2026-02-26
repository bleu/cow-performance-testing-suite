# CoW Performance Testing Suite

Comprehensive performance testing suite for the CoW Protocol Playground, enabling load testing, benchmarking, and regression detection using Anvil fork mode.

## Features

- **Load Generation**: Simulate realistic trading patterns with configurable strategies
- **Performance Benchmarking**: Measure order lifecycle, API performance, and resource utilization
- **Metrics & Visualization**: Prometheus exporters and Grafana dashboards
- **Regression Detection**: Statistical comparison against baselines
- **Fork Mode Testing**: Test against mainnet state using Anvil fork mode
- **Scenario Library**: Predefined scenarios from light to heavy loads
- **Flexible Configuration**: YAML-based scenarios with inheritance and composition

## Quick Start

### Prerequisites

- Python 3.11+
- Poetry (for dependency management)
- Docker and Docker Compose
- Ethereum RPC URL (Alchemy, Infura, etc.)

### Setup (5 Steps)

1. **Clone and install**
   ```bash
   git clone https://github.com/cowprotocol/cow-performance-testing-suite.git
   cd cow-performance-testing-suite
   poetry install && poetry shell
   ```

   Alternative without Poetry:
   ```bash
   python3 -m venv .venv && source .venv/bin/activate && pip install -e .
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and set: ETH_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY
   ```

3. **Start services**
   ```bash
   docker compose up -d
   ```
   > **Note**: First startup may show "unhealthy" errors while orderbook compiles
   > (takes 5-10 minutes). Check progress: `docker compose logs -f orderbook`

4. **Verify installation**
   ```bash
   cow-perf version
   ```

5. **Run your first test**
   ```bash
   cow-perf run --config configs/scenarios/light-load.yml
   ```

## Monitoring & Visualization

Prometheus metrics export is **enabled by default** (port 9091). To use the full monitoring stack:

1. **Start Prometheus & Grafana**
   ```bash
   docker compose --profile monitoring up -d
   ```

2. **Run a test** (metrics export automatically on port 9091)
   ```bash
   cow-perf run --config configs/scenarios/light-load.yml
   ```

3. **View dashboards** at http://localhost:3000 (default: admin/admin)
   - Performance Overview
   - API Performance
   - Resources
   - Comparison
   - Trader Activity

4. **Disable metrics export** (if needed)
   ```bash
   cow-perf run --config configs/scenarios/light-load.yml --prometheus-port 0
   ```

For detailed setup and troubleshooting, see [Development Guide](docs/development.md).

## Documentation

| Topic | Document |
|-------|----------|
| CLI Reference | [docs/cli.md](docs/cli.md) |
| Development Guide | [docs/development.md](docs/development.md) |
| Architecture | [docs/architecture.md](docs/architecture.md) |
| Order Generation API | [docs/order-generation.md](docs/order-generation.md) |
| Conditional Orders | [docs/conditional-orders.md](docs/conditional-orders.md) |
| User Simulation | [docs/user-simulation.md](docs/user-simulation.md) |

## Project Structure

```
cow-performance-testing-suite/
├── src/cow_performance/     # Core modules
│   ├── cli/                 # CLI commands (Typer)
│   ├── load_generation/     # Order generation, traders, Safe wallets
│   ├── benchmarking/        # Performance analysis
│   ├── metrics/             # Metrics collection
│   └── scenarios/           # Test scenarios
├── tests/                   # Unit, integration, and E2E tests
├── configs/                 # Configuration and scenario files
├── docs/                    # Documentation
└── docker/                  # Docker configuration
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting: `poetry run pytest && poetry run ruff check . && poetry run mypy .`
5. Submit a pull request

## Roadmap

- [x] **Milestone 1**: Project Setup & Load Generation Framework
- [ ] **Milestone 2**: User Simulation Module (TraderPool, Safe wallets, hooks)
- [ ] **Milestone 3**: CLI Tool Interface
- [ ] **Milestone 4**: Performance Benchmarking & Metrics
- [ ] **Milestone 5**: Advanced Features & Documentation

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/cowprotocol/cow-performance-testing-suite/issues)
- **Discussions**: [GitHub Discussions](https://github.com/cowprotocol/cow-performance-testing-suite/discussions)

## Acknowledgments

Built with love by the CoW Protocol team for comprehensive performance testing of the CoW Protocol Playground.
