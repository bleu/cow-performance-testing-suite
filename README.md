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
poetry run pytest tests/unit

# Run integration tests
poetry run pytest tests/integration

# Run with coverage
poetry run pytest --cov=src/cow_performance --cov-report=html
```

### Test Organization

- **Unit tests**: Test individual components in isolation
- **Integration tests**: Test component interactions
- **End-to-end tests**: Test complete workflows (coming in M5)

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

### Milestone 1: Load Generation Framework ✅ (Current)
- [x] Project setup and repository structure
- [ ] Fork mode environment setup
- [ ] Order generation engine
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
