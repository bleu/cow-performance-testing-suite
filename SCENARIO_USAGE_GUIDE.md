# Enhanced Scenarios - Usage Guide

## Overview

The enhanced scenario system provides:
- **Tags** for categorization and filtering
- **Metadata** with expected outcomes and resource requirements
- **Success Criteria** for automated pass/fail validation
- **Backward compatibility** with existing scenarios

## Quick Start

### 1. Validate a Scenario

```bash
cow-perf scenarios --validate configs/scenarios/enhanced/regression-test.yml
```

Output shows:
- Scenario details (name, description, version, tags)
- Metadata (expected orders, resource requirements)
- Success criteria (thresholds for pass/fail)
- Order type distribution

### 2. Programmatic Usage

```python
from pathlib import Path
from cow_performance.cli.commands.scenarios import load_scenario_from_yaml
from cow_performance.scenarios import (
    SuccessCriteriaValidator,
    display_validation_result,
)

# Load scenario
scenario = load_scenario_from_yaml(
    Path('configs/scenarios/enhanced/regression-test.yml')
)

# Access metadata
print(f"Expected orders: {scenario.metadata.expected_orders}")
print(f"Min memory: {scenario.metadata.resources.min_memory_gb}GB")
print(f"Tags: {scenario.tags}")

# Validate test results
if scenario.success_criteria:
    validator = SuccessCriteriaValidator(scenario.success_criteria)

    result = validator.validate(
        success_rate=0.95,
        p95_latency_seconds=8.0,
        error_rate=0.05,
        throughput_per_second=6.0,
    )

    # Display results
    display_validation_result(result)

    # Check if passed
    if result.passed:
        print("✅ All criteria met!")
    else:
        print(f"❌ {len(result.failures)} criteria failed")
        for failure in result.failures:
            print(f"  - {failure.message}")
```

### 3. Validate from Dictionary

```python
# Validate results from a dictionary (useful for integration)
results = {
    "success_rate": 0.95,
    "p95_latency_seconds": 8.0,
    "error_rate": 0.05,
    "throughput_per_second": 6.0,
}

result = validator.validate_from_dict(results)
```

## Available Scenarios

### Regression Test (CI/CD Optimized)
**File:** `configs/scenarios/enhanced/regression-test.yml`
**Tags:** regression, ci-cd, short, quick, automated
**Duration:** 2 minutes
**Purpose:** Fast CI/CD test for detecting performance degradation

**Success Criteria:**
- Min Success Rate: 90%
- Max P95 Latency: 15s
- Max Error Rate: 10%
- Min Throughput: 4.0 orders/s

**When to use:**
- Continuous integration pipelines
- Pre-commit hooks
- Pull request validation
- Quick smoke tests

### Sustained Load (Stability Test)
**File:** `configs/scenarios/enhanced/sustained-load.yml`
**Tags:** sustained, stability, long, endurance
**Duration:** 30 minutes
**Purpose:** Test system stability and detect memory leaks

**Success Criteria:**
- Min Success Rate: 95%
- Max P95 Latency: 10s
- Max Error Rate: 5%
- Min Throughput: 9.0 orders/s

**When to use:**
- Production readiness testing
- Memory leak detection
- Long-term stability validation
- Load testing before releases

### Large Orders (Edge Case)
**File:** `configs/scenarios/enhanced/large-orders.yml`
**Tags:** edge-case, large-orders, whale, short
**Duration:** 5 minutes
**Purpose:** Test handling of very large order amounts (100+ ETH)

**Success Criteria:**
- Min Success Rate: 85% (lower due to liquidity)
- Max P95 Latency: 20s
- Max Error Rate: 15%
- Min Throughput: 0.4 orders/s

**When to use:**
- Whale trader testing
- Liquidity constraint testing
- Edge case validation
- High-value transaction testing

### High-Frequency (Edge Case)
**File:** `configs/scenarios/enhanced/high-frequency.yml`
**Tags:** edge-case, high-frequency, stress, short
**Duration:** 3 minutes
**Purpose:** Test system under very high submission rate (100 orders/sec)

**Success Criteria:**
- Min Success Rate: 80%
- Max P95 Latency: 30s
- Max Error Rate: 20%
- Min Throughput: 80.0 orders/s

**When to use:**
- Stress testing
- Rate limiting validation
- Peak load testing
- HFT simulation

### Limit Orders Only (Edge Case)
**File:** `configs/scenarios/enhanced/limit-orders-only.yml`
**Tags:** edge-case, limit-orders, orderbook, medium
**Duration:** 10 minutes
**Purpose:** Test system with 100% limit orders (no market orders)

**Success Criteria:**
- Min Success Rate: 70% (many won't fill)
- Max P95 Latency: 20s
- Max Error Rate: 30%
- Min Throughput: 3.0 orders/s

**When to use:**
- Orderbook testing
- Limit order matching validation
- Price discovery testing
- Non-market order scenarios

## Creating Custom Scenarios

### Minimal Scenario
```yaml
name: my-test
description: My custom test scenario

# Required fields
num_traders: 10
duration: 60
trading_pattern: constant_rate
base_rate: 300.0

# Order ratios (must sum to 1.0)
market_order_ratio: 0.5
limit_order_ratio: 0.5
twap_order_ratio: 0.0
stop_loss_order_ratio: 0.0
good_after_time_order_ratio: 0.0
```

### Full-Featured Scenario
```yaml
name: my-test
description: My custom test scenario
version: "1.0"

# Tags for categorization
tags:
  - custom
  - baseline
  - medium-load

# Metadata
metadata:
  expected_orders: 600
  expected_duration_seconds: 120
  resources:
    min_memory_gb: 2.0
    min_cpu_cores: 2
    recommended_memory_gb: 4.0
    recommended_cpu_cores: 4

# Success criteria
success_criteria:
  min_success_rate: 0.90
  max_p95_latency_seconds: 15.0
  max_error_rate: 0.10
  min_throughput_per_second: 4.0

# Test configuration
num_traders: 10
duration: 120
startup_interval: 0.1

# Order type distribution
market_order_ratio: 0.5
limit_order_ratio: 0.5
twap_order_ratio: 0.0
stop_loss_order_ratio: 0.0
good_after_time_order_ratio: 0.0

# Trading pattern
trading_pattern: constant_rate
base_rate: 300.0  # 5 orders/sec
```

## Success Criteria Guidelines

### Setting Thresholds

**Min Success Rate:**
- Regression tests: 0.90 (90%)
- Production tests: 0.95 (95%)
- Edge cases: 0.70-0.85 (lower acceptable)

**Max P95 Latency:**
- Fast tests: 15-20s
- Normal tests: 10-15s
- Strict tests: 5-10s
- Edge cases: 20-30s (higher acceptable)

**Max Error Rate:**
- Regression tests: 0.10 (10%)
- Production tests: 0.05 (5%)
- Edge cases: 0.15-0.30 (higher acceptable)

**Min Throughput:**
- Calculate: `(num_traders * base_rate / 60) * 0.8`
- Example: 10 traders * 300/60 = 50 orders/min = ~0.83 orders/sec
- Set threshold at 80% of expected: 0.66 orders/sec

## Tag System

### Standard Tags

**By Duration:**
- `short` - < 5 minutes
- `medium` - 5-15 minutes
- `long` - > 15 minutes

**By Load:**
- `light-load` - Low intensity
- `medium-load` - Normal intensity
- `heavy-load` - High intensity

**By Purpose:**
- `regression` - CI/CD regression testing
- `stress` - Stress testing
- `stability` - Long-term stability
- `baseline` - Standard benchmarking
- `edge-case` - Edge case validation

**By Feature:**
- `ci-cd` - CI/CD optimized
- `automated` - Automated testing
- `manual` - Manual testing
- `quick` - Quick validation

## Integration Examples

### CI/CD Pipeline

```yaml
# .github/workflows/performance-regression.yml
name: Performance Regression Test

on: [pull_request]

jobs:
  regression-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup
        run: |
          # Setup steps...

      - name: Run regression test
        run: |
          cow-perf run \
            --config configs/scenarios/enhanced/regression-test.yml \
            --baseline main \
            --fail-on-regression

      - name: Validate success criteria
        run: |
          # Use validator to check results
          python scripts/validate_results.py
```

### Python Test Integration

```python
import pytest
from pathlib import Path
from cow_performance.cli.commands.scenarios import load_scenario_from_yaml
from cow_performance.scenarios import SuccessCriteriaValidator

def test_performance_meets_criteria():
    """Test that performance meets success criteria."""
    # Load scenario
    scenario = load_scenario_from_yaml(
        Path('configs/scenarios/enhanced/regression-test.yml')
    )

    # Run test (mock for example)
    results = run_performance_test(scenario)

    # Validate
    validator = SuccessCriteriaValidator(scenario.success_criteria)
    result = validator.validate_from_dict(results)

    # Assert
    assert result.passed, f"Performance test failed: {result.failures}"
```

## Best Practices

1. **Always set success criteria** for automated tests
2. **Use tags consistently** for easy filtering
3. **Document metadata** for resource planning
4. **Version scenarios** when making significant changes
5. **Test scenarios** before using in CI/CD
6. **Set realistic thresholds** based on baseline performance
7. **Include descriptions** explaining scenario purpose

## Troubleshooting

### Validation Always Fails
- Check if thresholds are realistic
- Run test manually to see actual values
- Compare against baseline performance
- Consider edge cases (liquidity, load)

### Cannot Load Scenario
- Verify YAML syntax is correct
- Ensure all required fields present
- Check file path is correct
- Validate order ratios sum to 1.0

### Success Criteria Not Working
- Ensure scenario has `success_criteria` section
- Check that validator receives correct metric names
- Verify metrics dictionary has correct keys
- Test validator separately with known values

## Next Steps

See `thoughts/plans/m4-issue-14-predefined-scenarios-plan.md` for remaining work:
- Phase 4: Per-scenario documentation
- Phase 5: CLI tag filtering
- Phase 7: CI/CD integration guide
