# M1 - Issue 02: Fork Mode Environment Setup - ✅ COMPLETE

**Date Completed**: 2026-01-16
**Status**: ✅ All Components Configured

---

## 🎯 What M1-Issue-02 Accomplished

**Purpose**: Set up the Docker Compose environment with Anvil fork mode and CoW Protocol services for realistic performance testing

**Scope**: Infrastructure setup for testing against mainnet state without actual mainnet interaction

---

## ✅ What Was Created

### 1. Docker Compose Configuration (1 file)
- `docker-compose.yml` (290 lines)
  - Anvil fork mode blockchain
  - PostgreSQL database
  - CoW Protocol services (Orderbook, Autopilot, Driver, Baseline Solver)
  - Monitoring stack (Prometheus, Grafana) with optional profile
  - Health checks for all services
  - Proper service dependencies

### 2. Environment Configuration (1 file)
- `.env.example` (95 lines)
  - Blockchain configuration (RPC URL, chain ID)
  - Database credentials
  - CoW Protocol settings
  - Performance testing parameters
  - Token addresses (mainnet)
  - Logging configuration

### 3. Service Configuration Files (3 files)
- `configs/driver.toml` (88 lines)
  - Driver service configuration
  - Solver connection settings
  - Transaction submission rules
  - Smart contract addresses
  - Liquidity sources (Uniswap V2)

- `configs/baseline.toml` (23 lines)
  - Baseline solver configuration
  - Routing parameters
  - Base tokens for multi-hop swaps

- `configs/prometheus.yml` (65 lines)
- `configs/grafana-datasource.yml` (16 lines)
- `configs/grafana-dashboard.yml` (10 lines)
  - Monitoring configuration

### 4. Git Submodule (1 submodule)
- `services/` - CoW Protocol services repository
  - Commit: `04f4e63687263ab3f1029197b175ec3be8f0a20e`
  - Version: v2.313.1-468-g04f4e6368

### 5. Documentation Updates
- `README.md` - Added comprehensive "Fork Mode Environment Setup" section (160+ lines)
  - Prerequisites
  - Initial setup steps
  - Service URLs table
  - Verification commands
  - Troubleshooting guide
  - Environment management

---

## 📦 Docker Services Configured

### Core Services:
1. **chain** (Anvil) - Mainnet fork at http://localhost:8545
2. **db** (PostgreSQL 16) - Database at localhost:5432
3. **db-migrations** (Flyway) - Automatic database migrations
4. **orderbook** - CoW Protocol orderbook API at http://localhost:8080
5. **autopilot** - Solver auction orchestrator (metrics at :9589)
6. **driver** - Autopilot-solver translator at http://localhost:9000
7. **baseline** - AMM-based solver at http://localhost:9001

### Monitoring Services (Optional Profile):
8. **prometheus** - Metrics collector at http://localhost:9090
9. **grafana** - Visualization at http://localhost:3000

---

## 🔧 How It Works

### Fork Mode Architecture:
```
ETH Mainnet (via RPC)
        ↓
    Anvil Fork
        ↓
┌───────────────────┐
│   PostgreSQL DB   │
└───────────────────┘
        ↓
┌───────────────────┐
│   Orderbook API   │ ← Orders submitted here
└───────────────────┘
        ↓
┌───────────────────┐
│    Autopilot      │ ← Orchestrates auctions
└───────────────────┘
        ↓
┌───────────────────┐
│      Driver       │ ← Translates requests
└───────────────────┘
        ↓
┌───────────────────┐
│  Baseline Solver  │ ← Finds optimal routes
└───────────────────┘
        ↓
  Settlement on Fork
```

### Key Features:
- **Realistic Testing**: Uses actual mainnet state and liquidity
- **No Gas Costs**: Transactions on forked chain are free
- **Deterministic**: Same fork point = same results
- **Fast**: Instant block mining (1s block time)
- **Isolated**: No risk to mainnet

---

## 🚀 Quick Start

### 1. Configure Environment:
```bash
cp .env.example .env
# Edit .env and set ETH_RPC_URL to your RPC endpoint
```

### 2. Start Services:
```bash
# Clone with submodules
git submodule update --init --recursive

# Start core services
docker compose up -d

# Or with monitoring
docker compose --profile monitoring up -d
```

### 3. Verify:
```bash
# Check all services
docker compose ps

# Test Anvil
cast block-number --rpc-url http://localhost:8545

# Test Orderbook
curl http://localhost:8080/api/v1/version
```

---

## ✅ Acceptance Criteria Status

From M1-Issue-02 requirements:

✅ **Docker Compose configuration created**
- Complete docker-compose.yml with all services
- Health checks configured
- Service dependencies properly set

✅ **Anvil fork mode configured**
- Fork URL configurable via environment
- Authenticator contract patched for testing
- 1-second block time
- 30M gas limit

✅ **CoW Protocol services integrated**
- Orderbook API
- Autopilot
- Driver
- Baseline Solver
- All built from official cowprotocol/services repo

✅ **Testing environment validation**
- Service health checks
- Database connectivity
- API endpoints accessible
- Documented verification steps

---

## 📋 Configuration Summary

### Environment Variables Required:
- `ETH_RPC_URL` - Mainnet RPC endpoint (Alchemy, Infura, etc.)
- `POSTGRES_USER` - Database user (default: postgres)
- `POSTGRES_PASSWORD` - Database password (default: password)

### Optional Variables:
- `SOLVER_ADDRESS` - Solver account address
- `RUST_LOG` - Logging level
- `BLOCK_TIME` - Anvil block time

### Ports Used:
- **8545** - Anvil RPC
- **5432** - PostgreSQL
- **8080** - Orderbook API
- **9000** - Driver
- **9001** - Baseline Solver
- **9586** - Orderbook metrics
- **9589** - Autopilot metrics
- **9090** - Prometheus (optional)
- **3000** - Grafana (optional)

---

## 🛠️ What Can Be Done Now

With M1-Issue-02 complete, you can:

✅ **Start the fork mode environment**
✅ **Submit orders to the orderbook API**
✅ **Monitor service metrics**
✅ **Test settlement flows**
✅ **Develop performance tests against real infrastructure**

---

## ⏭️ What's Next

### M1-Issue-03: Order Generation Engine
- Create order generation utilities
- Implement EIP-712 signing
- Support multiple order types
- Handle token approvals

### M1-Issue-04: User Simulation Module
- Trader account management
- Balance funding
- Token approval handling
- Account state tracking

---

## 📊 Files Created

**Configuration Files**: 6
- docker-compose.yml
- .env.example
- configs/driver.toml
- configs/baseline.toml
- configs/prometheus.yml
- configs/grafana-datasource.yml
- configs/grafana-dashboard.yml

**Git Submodules**: 1
- services/ (CoW Protocol services)

**Documentation**: 1
- Updated README.md with Fork Mode section

**Total Lines Added**: ~700+ lines

---

## 🎓 Key Learnings

### Docker Compose Best Practices:
- Used health checks for service readiness
- Configured proper service dependencies
- Separated optional services with profiles
- Mounted configuration as read-only volumes

### CoW Protocol Integration:
- Services built from official repository
- Configuration follows playground patterns
- Uses standard mainnet contract addresses
- Authenticator patched for unrestricted testing

### Fork Mode Benefits:
- Test against real liquidity pools
- No mainnet gas costs
- Deterministic and reproducible
- Fast feedback loop (1s blocks)

---

## 💡 Important Notes

### First Startup Time:
- **10-15 minutes** for initial Docker image builds
- Subsequent startups: ~30 seconds

### Resource Requirements:
- **RAM**: 8GB minimum
- **Disk**: 5GB for Docker images
- **CPU**: Multi-core recommended

### RPC Requirements:
- Must support mainnet fork
- Should support archive queries
- Rate limits should allow sustained calls

---

## ✅ M1-Issue-02 Complete!

All infrastructure is ready for performance testing development. The fork mode environment provides a realistic, cost-free testing ground for developing and validating the performance testing suite.

**Status**: Ready for M1-Issue-03 (Order Generation Engine)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
