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

## Reports & Baselines

Save performance baselines and generate comprehensive reports with regression detection.

### Save Baseline After Test

Run a test and automatically save the results as a baseline for future comparisons:

```bash
# Run test and save as baseline
cow-perf run --config configs/scenarios/light-load.yml \
  --save-baseline "v1.0" \
  --baseline-description "Production baseline" \
  --baseline-tags "production,release"
```

**Saved to**: `.cow-perf/baselines/{uuid}.json`

### Generate Reports

Generate performance reports from saved baselines in multiple formats:

```bash
# Text report to console (default)
cow-perf report generate v1.0

# Save report to file (.cow-perf/reports/)
cow-perf report generate v1.0 --save

# Markdown report (GitHub-friendly)
cow-perf report generate v1.0 -f markdown --save

# JSON report (machine-readable)
cow-perf report generate v1.0 -f json --save

# With CSV exports
cow-perf report generate v1.0 --save --export-csv
```

**Saved to**:
- Reports: `.cow-perf/reports/report-{baseline}-{timestamp}.{format}`
- CSV files: `.cow-perf/reports/csv/{baseline}/summary.csv`, `latencies.csv`, `recommendations.csv`

### Compare Baselines (Regression Detection)

Compare two baselines to detect performance regressions or improvements:

```bash
# Compare current against previous baseline
cow-perf report generate v2.0 --compare v1.0 --save

# With markdown format for GitHub PRs
cow-perf report generate v2.0 --compare v1.0 -f markdown --save
```

The comparison report shows:
- ✅ **Improvements**: Metrics that got better
- ⚠️ **Regressions**: Metrics that got worse (with severity: minor/major/critical)
- 📊 **Percent changes**: For all key metrics
- 🔧 **Recommendations**: Actionable insights based on the comparison

### Manage Baselines

```bash
# List all saved baselines
cow-perf baselines --list

# Show detailed baseline info
cow-perf baselines --show v1.0

# Delete old baseline
cow-perf baselines --delete old-baseline
```

### Multiple Solver Tracking

**All solver containers are automatically tracked** - no configuration needed!

The system uses pattern matching to discover containers:
- Any container with `solver` in its name is tracked (e.g., `solver-baseline-1`, `solver-quasimodo-1`)
- Each solver gets separate resource metrics (CPU, memory, network I/O)
- Reports show per-solver performance

**Supported solver types**:
- `solver-baseline-*` - Baseline solver instances
- `solver-quasimodo-*` - Quasimodo solver instances
- `solver-{any-type}-*` - Any other solver type

**Adding more solvers**:
1. Add new solver services to `docker-compose.yml` (e.g., `solver-baseline-4`, `solver-quasimodo-1`)
2. Start containers: `docker compose up -d`
3. Run test: `cow-perf run --save-baseline "test-name"`
4. Reports automatically include all solvers!

**Example report output**:
```
Resource Utilization:
  Container              CPU(P95)  Memory(P95)
  -----------------------------------------------
  solver-baseline-1        38.8%       11.0%
  solver-baseline-2        43.8%       12.0%
  solver-baseline-3        48.8%       13.0%
  solver-quasimodo-1       35.2%       10.5%
  solver-quasimodo-2       41.1%       11.8%
```

When comparing baselines, per-solver improvements/regressions are shown:
```
Improvements:
  - resource_solver-baseline-1_cpu: -51.5% (improved)
  - resource_solver-baseline-2_cpu: -9.1% (improved)
  - resource_solver-quasimodo-1_cpu: -12.3% (improved)
```

### Complete Workflow Example

```bash
# 1. Run initial test and save baseline
cow-perf run --config configs/scenarios/medium-load.yml \
  --save-baseline "before-optimization" \
  --baseline-description "Performance before optimization work"

# 2. Make code changes, run new test
cow-perf run --config configs/scenarios/medium-load.yml \
  --save-baseline "after-optimization" \
  --baseline-description "Performance after optimization"

# 3. Generate comparison report
cow-perf report generate after-optimization \
  --compare before-optimization \
  -f markdown \
  --save \
  --export-csv

# 4. View results
cat .cow-perf/reports/report-after-optimization-vs-before-optimization-*.md
```

All files are saved in your project directory under `.cow-perf/`:
```
.cow-perf/
├── baselines/              # Saved performance baselines
├── reports/                # Generated reports
│   ├── report-*.txt
│   ├── report-*.md
│   ├── report-*.json
│   └── csv/               # CSV exports
│       └── {baseline}/
│           ├── summary.csv
│           ├── latencies.csv
│           └── recommendations.csv
└── results/               # Raw test results
```

See `.cow-perf/README.md` for detailed documentation on the data directory structure.

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

## Disk Management

The Docker environment is optimized to prevent excessive disk usage, but monitoring is still recommended:

### Built-in Protections

- **Chain container (Anvil)**: Uses `--prune-history` flag to keep state in process memory only (no disk accumulation)
- **Container logs**: Limited to 10MB per file, max 3 files (30MB total per service)
- **Prometheus data**: Retention limited to 7 days and 1GB
- **Rust build artifacts**: Stored in Docker volumes (not on host disk)

### Monitoring Disk Usage

```bash
# Check Docker disk usage
docker system df

# Monitor specific container disk usage
docker stats --no-stream
```

### Cleanup Options

**Quick cleanup** (recommended for regular use):
```bash
# Stop containers (preserves images and volumes)
docker compose down

# Remove stopped containers and unused images
docker system prune -f
```

**Deep cleanup** (if disk space is critical):
```bash
# Use the automated cleanup script
./hack/cleanup-docker.sh

# Or manual cleanup with volumes (⚠️  data loss)
docker compose down -v
docker system prune -a -f --volumes
```

**After cleanup**, restart services:
```bash
docker compose up -d
```

> **Note**: First startup after cleanup may be slower due to image rebuilding and database migrations.

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
