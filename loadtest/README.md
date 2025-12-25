# Load Testing

Performance and load testing infrastructure for the Ingredient Analysis API.

## Overview

- **Peak Load Target:** 2,000 requests/minute (33.33 RPS)
- **Test Scenarios:** Steady, Ramp, Spike
- **Dashboard:** Integrated with Streamlit desktop app

## Quick Start

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies (if not already)
pip install requests

# Run basic load test
python loadtest/load_test.py --target https://api.zeroleaf.dev

# View results in dashboard
# Navigate to "Load Tests" from the main app
```

## Usage

### Command Line Options

```bash
python loadtest/load_test.py [OPTIONS]

Options:
  --target, -t      Target API URL (default: https://api.zeroleaf.dev)
  --duration, -d    Test duration in seconds (default: 60)
  --max-rps         Max requests per second (default: 33.33, capped at 2000/min)
  --scenario, -s    Load pattern: steady, ramp, spike (default: steady)
  --workers, -w     Concurrent workers (default: 10)
  --output-dir, -o  Output directory (default: loadtest/results)
```

### Examples

```bash
# 2-minute steady load test
python loadtest/load_test.py --target https://api.zeroleaf.dev --duration 120

# Ramp-up test (gradual increase from 10% to 100%)
python loadtest/load_test.py --scenario ramp --duration 180

# Spike test (30% baseline with 100% bursts)
python loadtest/load_test.py --scenario spike --duration 120

# Lower RPS for initial testing
python loadtest/load_test.py --max-rps 5 --duration 60
```

## Test Scenarios

### Steady
Constant load at the specified RPS throughout the test.
Best for: Measuring sustained performance.

### Ramp
Linear increase from 10% to 100% of max RPS over the duration.
Best for: Finding breaking points.

### Spike
30% baseline load with 100% spikes at 25%, 50%, and 75% of duration.
Best for: Testing burst handling.

## Results

Results are saved to `loadtest/results/`:

- `latest.json` - Most recent test results (used by dashboard)
- `history.json` - Summary of last 50 tests
- `load_YYYYMMDD_HHMMSS.json` - Individual test results

### Metrics Collected

| Metric | Description |
|--------|-------------|
| Total Requests | Number of requests sent |
| Success Rate | Percentage of successful responses |
| RPS | Actual requests per second achieved |
| P50/P95/P99 | Response time percentiles |
| Error Rate | Percentage of failed requests |

## Dashboard

Access the dashboard from the main Streamlit app:
1. Open the desktop app
2. Click "Load Tests" in the navigation

Or run standalone:
```bash
streamlit run loadtest/dashboard.py
```

## Requirements

The load test uses `requests` for HTTP calls. For large-scale tests, consider:

```bash
pip install locust  # For distributed testing
```

## API Rate Limits

The load tester is capped at 2,000 requests/minute to prevent overwhelming the production API. Adjust `--max-rps` for lighter tests:

| RPS | Requests/Minute |
|-----|-----------------|
| 5   | 300 |
| 10  | 600 |
| 20  | 1,200 |
| 33.33 | 2,000 (max) |
