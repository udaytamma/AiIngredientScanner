#!/usr/bin/env python3
"""Load testing script for Ingredient Analysis API.

Uses Locust for distributed load testing with configurable parameters.
Results are saved to JSON for dashboard visualization.

Peak load: 2000 requests/minute (~33 requests/second)

Usage:
    # Run load test (headless mode)
    python loadtest/load_test.py --target https://api.zeroleaf.dev --duration 60

    # Run with Locust web UI
    locust -f loadtest/load_test.py --host https://api.zeroleaf.dev

    # Run specific scenario
    python loadtest/load_test.py --target https://api.zeroleaf.dev --scenario spike
"""

import argparse
import json
import os
import sys
import time
import random
import statistics
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from typing import Optional

import requests

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# Test data - realistic ingredient lists
TEST_INGREDIENTS = [
    # Simple (1-3 ingredients)
    ["Water", "Glycerin"],
    ["Sodium Lauryl Sulfate"],
    ["Retinol", "Vitamin E", "Aloe Vera"],

    # Medium (4-6 ingredients)
    ["Water", "Glycerin", "Sodium Chloride", "Citric Acid"],
    ["Salicylic Acid", "Niacinamide", "Hyaluronic Acid", "Vitamin C", "Retinol"],
    ["Coconut Oil", "Shea Butter", "Beeswax", "Vitamin E", "Lavender Oil"],

    # Complex (7+ ingredients)
    [
        "Water", "Glycerin", "Cetyl Alcohol", "Dimethicone", "Sodium Hyaluronate",
        "Tocopherol", "Phenoxyethanol", "Fragrance"
    ],
    [
        "Aqua", "Sodium Laureth Sulfate", "Cocamidopropyl Betaine", "Glycerin",
        "Sodium Chloride", "Citric Acid", "Parfum", "Limonene", "Linalool"
    ],
    [
        "Water", "Isopropyl Palmitate", "Glycerin", "Cetearyl Alcohol",
        "Dimethicone", "Petrolatum", "Sodium Hyaluronate", "Niacinamide",
        "Tocopheryl Acetate", "Panthenol", "Phenoxyethanol", "Methylparaben"
    ],
]

TEST_ALLERGIES = [
    [],
    ["fragrance"],
    ["sulfates", "parabens"],
    ["fragrance", "formaldehyde", "sulfates"],
]

TEST_SKIN_TYPES = ["normal", "dry", "oily", "combination", "sensitive"]
TEST_EXPERTISE = ["beginner", "expert"]


@dataclass
class RequestResult:
    """Single request result."""
    timestamp: str
    duration_ms: float
    status_code: int
    success: bool
    error: Optional[str] = None
    ingredient_count: int = 0


@dataclass
class LoadTestResult:
    """Complete load test results."""
    test_id: str
    target_url: str
    scenario: str
    start_time: str
    end_time: str
    duration_seconds: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    requests_per_second: float
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    error_rate_percent: float
    errors: dict
    request_log: list


def make_request(base_url: str, timeout: int = 120) -> RequestResult:
    """Make a single API request with random test data.

    Args:
        base_url: API base URL.
        timeout: Request timeout in seconds.

    Returns:
        RequestResult with timing and status.
    """
    timestamp = datetime.now().isoformat()
    ingredients_list = random.choice(TEST_INGREDIENTS)
    # API expects ingredients as comma-separated string, not list
    ingredients_str = ", ".join(ingredients_list)

    payload = {
        "ingredients": ingredients_str,
        "product_name": f"Test Product {random.randint(1000, 9999)}",
        "allergies": random.choice(TEST_ALLERGIES),
        "skin_type": random.choice(TEST_SKIN_TYPES),
        "expertise": random.choice(TEST_EXPERTISE),
    }

    url = f"{base_url.rstrip('/')}/analyze"

    start = time.perf_counter()
    try:
        response = requests.post(
            url,
            json=payload,
            timeout=timeout,
            headers={"Content-Type": "application/json"}
        )
        duration_ms = (time.perf_counter() - start) * 1000

        return RequestResult(
            timestamp=timestamp,
            duration_ms=round(duration_ms, 2),
            status_code=response.status_code,
            success=response.status_code == 200,
            error=None if response.status_code == 200 else response.text[:200],
            ingredient_count=len(ingredients_list),
        )

    except requests.Timeout:
        duration_ms = (time.perf_counter() - start) * 1000
        return RequestResult(
            timestamp=timestamp,
            duration_ms=round(duration_ms, 2),
            status_code=0,
            success=False,
            error="Request timeout",
            ingredient_count=len(ingredients_list),
        )
    except Exception as e:
        duration_ms = (time.perf_counter() - start) * 1000
        return RequestResult(
            timestamp=timestamp,
            duration_ms=round(duration_ms, 2),
            status_code=0,
            success=False,
            error=str(e)[:200],
            ingredient_count=len(ingredients_list),
        )


def run_load_test(
    target_url: str,
    duration_seconds: int = 60,
    max_rps: float = 33.33,  # 2000/minute = 33.33/second
    scenario: str = "steady",
    workers: int = 10,
) -> LoadTestResult:
    """Run load test against the API.

    Args:
        target_url: API base URL.
        duration_seconds: Test duration.
        max_rps: Maximum requests per second (capped at 33.33 = 2000/min).
        scenario: Load pattern (steady, ramp, spike).
        workers: Number of concurrent workers.

    Returns:
        LoadTestResult with all metrics.
    """
    test_id = f"load_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    start_time = datetime.now()

    print(f"\n{'='*60}")
    print(f"Load Test: {test_id}")
    print(f"Target: {target_url}")
    print(f"Scenario: {scenario}")
    print(f"Duration: {duration_seconds}s")
    print(f"Max RPS: {max_rps:.2f} ({max_rps * 60:.0f}/min)")
    print(f"Workers: {workers}")
    print(f"{'='*60}\n")

    results: list[RequestResult] = []
    errors: dict[str, int] = {}

    # Calculate request intervals based on scenario
    def get_current_rps(elapsed: float) -> float:
        if scenario == "steady":
            return max_rps
        elif scenario == "ramp":
            # Linear ramp from 10% to 100% over duration
            progress = min(elapsed / duration_seconds, 1.0)
            return max_rps * (0.1 + 0.9 * progress)
        elif scenario == "spike":
            # Normal load with spikes at 25%, 50%, 75%
            progress = elapsed / duration_seconds
            if 0.24 < progress < 0.26 or 0.49 < progress < 0.51 or 0.74 < progress < 0.76:
                return max_rps  # Full load during spikes
            return max_rps * 0.3  # 30% baseline
        return max_rps

    test_start = time.perf_counter()
    request_count = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = []

        while (time.perf_counter() - test_start) < duration_seconds:
            elapsed = time.perf_counter() - test_start
            current_rps = get_current_rps(elapsed)

            # Submit request
            futures.append(executor.submit(make_request, target_url))
            request_count += 1

            # Calculate sleep to maintain target RPS
            expected_time = request_count / current_rps
            actual_time = time.perf_counter() - test_start
            sleep_time = expected_time - actual_time

            if sleep_time > 0:
                time.sleep(sleep_time)

            # Progress update every 10 seconds
            if int(elapsed) % 10 == 0 and int(elapsed) > 0:
                completed = sum(1 for f in futures if f.done())
                print(f"  [{int(elapsed)}s] Sent: {request_count}, Completed: {completed}, "
                      f"Current RPS: {current_rps:.1f}")

        # Wait for remaining requests (each request can take 30-60s due to LLM processing)
        print("\nWaiting for pending requests...")
        for future in as_completed(futures, timeout=600):
            try:
                result = future.result()
                results.append(result)

                if not result.success and result.error:
                    error_key = result.error[:50]
                    errors[error_key] = errors.get(error_key, 0) + 1

            except Exception as e:
                errors[str(e)[:50]] = errors.get(str(e)[:50], 0) + 1

    end_time = datetime.now()
    actual_duration = (end_time - start_time).total_seconds()

    # Calculate metrics
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    response_times = [r.duration_ms for r in results]
    response_times.sort()

    def percentile(data: list, p: float) -> float:
        if not data:
            return 0
        k = (len(data) - 1) * p / 100
        f = int(k)
        c = f + 1 if f + 1 < len(data) else f
        return data[f] + (k - f) * (data[c] - data[f]) if c != f else data[f]

    result = LoadTestResult(
        test_id=test_id,
        target_url=target_url,
        scenario=scenario,
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat(),
        duration_seconds=round(actual_duration, 2),
        total_requests=len(results),
        successful_requests=len(successful),
        failed_requests=len(failed),
        requests_per_second=round(len(results) / actual_duration, 2) if actual_duration > 0 else 0,
        avg_response_time_ms=round(statistics.mean(response_times), 2) if response_times else 0,
        min_response_time_ms=round(min(response_times), 2) if response_times else 0,
        max_response_time_ms=round(max(response_times), 2) if response_times else 0,
        p50_response_time_ms=round(percentile(response_times, 50), 2),
        p95_response_time_ms=round(percentile(response_times, 95), 2),
        p99_response_time_ms=round(percentile(response_times, 99), 2),
        error_rate_percent=round(len(failed) / len(results) * 100, 2) if results else 0,
        errors=errors,
        request_log=[asdict(r) for r in results[-100:]],  # Keep last 100 for detail
    )

    return result


def save_results(result: LoadTestResult, output_dir: Path) -> Path:
    """Save test results to JSON file.

    Args:
        result: Test results.
        output_dir: Output directory.

    Returns:
        Path to saved file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save individual result
    result_file = output_dir / f"{result.test_id}.json"
    with open(result_file, "w") as f:
        json.dump(asdict(result), f, indent=2)

    # Update latest.json for dashboard
    latest_file = output_dir / "latest.json"
    with open(latest_file, "w") as f:
        json.dump(asdict(result), f, indent=2)

    # Update history.json (keep last 50 tests)
    history_file = output_dir / "history.json"
    history = []
    if history_file.exists():
        with open(history_file) as f:
            history = json.load(f)

    # Add summary (not full request log)
    summary = asdict(result)
    summary.pop("request_log", None)
    history.insert(0, summary)
    history = history[:50]

    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)

    return result_file


def print_results(result: LoadTestResult) -> None:
    """Print formatted test results."""
    print(f"\n{'='*60}")
    print("LOAD TEST RESULTS")
    print(f"{'='*60}")
    print(f"Test ID:        {result.test_id}")
    print(f"Target:         {result.target_url}")
    print(f"Scenario:       {result.scenario}")
    print(f"Duration:       {result.duration_seconds}s")
    print()
    print("THROUGHPUT:")
    print(f"  Total Requests:     {result.total_requests}")
    print(f"  Successful:         {result.successful_requests}")
    print(f"  Failed:             {result.failed_requests}")
    print(f"  Requests/Second:    {result.requests_per_second}")
    print(f"  Error Rate:         {result.error_rate_percent}%")
    print()
    print("RESPONSE TIMES (ms):")
    print(f"  Average:   {result.avg_response_time_ms}")
    print(f"  Min:       {result.min_response_time_ms}")
    print(f"  Max:       {result.max_response_time_ms}")
    print(f"  P50:       {result.p50_response_time_ms}")
    print(f"  P95:       {result.p95_response_time_ms}")
    print(f"  P99:       {result.p99_response_time_ms}")

    if result.errors:
        print()
        print("ERRORS:")
        for error, count in sorted(result.errors.items(), key=lambda x: -x[1])[:5]:
            print(f"  [{count}x] {error}")

    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Load test Ingredient Analysis API")
    parser.add_argument(
        "--target", "-t",
        default="https://api.zeroleaf.dev",
        help="Target API URL"
    )
    parser.add_argument(
        "--duration", "-d",
        type=int,
        default=60,
        help="Test duration in seconds (default: 60)"
    )
    parser.add_argument(
        "--max-rps",
        type=float,
        default=33.33,
        help="Max requests per second (default: 33.33 = 2000/min)"
    )
    parser.add_argument(
        "--scenario", "-s",
        choices=["steady", "ramp", "spike"],
        default="steady",
        help="Load pattern: steady, ramp (gradual increase), spike (periodic bursts)"
    )
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=10,
        help="Number of concurrent workers (default: 10)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=Path(__file__).parent / "results",
        help="Output directory for results"
    )

    args = parser.parse_args()

    # Cap max RPS at 2000/minute
    if args.max_rps > 33.34:
        print(f"Warning: Max RPS capped at 33.33 (2000/min)")
        args.max_rps = 33.33

    # Run test
    result = run_load_test(
        target_url=args.target,
        duration_seconds=args.duration,
        max_rps=args.max_rps,
        scenario=args.scenario,
        workers=args.workers,
    )

    # Save and print results
    result_file = save_results(result, args.output_dir)
    print_results(result)
    print(f"Results saved to: {result_file}")


if __name__ == "__main__":
    main()
