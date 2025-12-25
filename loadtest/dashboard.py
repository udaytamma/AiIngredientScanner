"""Load Test Dashboard - Streamlit page for viewing load test results.

This module provides a Streamlit page component that can be embedded
in the main app to display load test results.
"""

import json
from datetime import datetime
from pathlib import Path

import streamlit as st


RESULTS_DIR = Path(__file__).parent / "results"


def get_status_color(error_rate: float) -> str:
    """Get color based on error rate."""
    if error_rate == 0:
        return "#28a745"  # Green
    elif error_rate < 5:
        return "#fd7e14"  # Orange
    else:
        return "#dc3545"  # Red


def get_response_time_color(p95: float) -> str:
    """Get color based on P95 response time."""
    if p95 < 5000:  # < 5s
        return "#28a745"
    elif p95 < 15000:  # < 15s
        return "#fd7e14"
    else:
        return "#dc3545"


def render_load_test_dashboard() -> None:
    """Render the load test dashboard page."""
    st.title("Load Test Dashboard")
    st.markdown("View performance metrics from load testing the Ingredient Analysis API")

    # Check for results
    if not RESULTS_DIR.exists():
        st.warning("No load test results found. Run a load test first.")
        st.code("python loadtest/load_test.py --target https://api.zeroleaf.dev")
        return

    # Load latest results
    latest_file = RESULTS_DIR / "latest.json"
    history_file = RESULTS_DIR / "history.json"

    if not latest_file.exists():
        st.warning("No load test results found. Run a load test first.")
        return

    with open(latest_file) as f:
        latest = json.load(f)

    # Header with test info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Test ID", latest["test_id"])
    with col2:
        st.metric("Scenario", latest["scenario"].title())
    with col3:
        st.metric("Duration", f"{latest['duration_seconds']}s")

    st.markdown(f"**Target:** `{latest['target_url']}`")
    st.markdown(f"**Tested:** {latest['start_time'][:19].replace('T', ' ')}")

    st.divider()

    # Key metrics
    st.subheader("Key Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        error_color = get_status_color(latest["error_rate_percent"])
        st.markdown(f"""
        <div style="background:#1e1e1e;padding:15px;border-radius:8px;border-left:4px solid {error_color};">
            <div style="color:#888;font-size:12px;">Success Rate</div>
            <div style="font-size:28px;font-weight:bold;color:{error_color};">
                {100 - latest["error_rate_percent"]:.1f}%
            </div>
            <div style="color:#666;font-size:11px;">
                {latest["successful_requests"]} / {latest["total_requests"]} requests
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="background:#1e1e1e;padding:15px;border-radius:8px;border-left:4px solid #0d6efd;">
            <div style="color:#888;font-size:12px;">Throughput</div>
            <div style="font-size:28px;font-weight:bold;color:#0d6efd;">
                {latest["requests_per_second"]:.1f}
            </div>
            <div style="color:#666;font-size:11px;">
                requests/second
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        p95_color = get_response_time_color(latest["p95_response_time_ms"])
        st.markdown(f"""
        <div style="background:#1e1e1e;padding:15px;border-radius:8px;border-left:4px solid {p95_color};">
            <div style="color:#888;font-size:12px;">P95 Response Time</div>
            <div style="font-size:28px;font-weight:bold;color:{p95_color};">
                {latest["p95_response_time_ms"]/1000:.1f}s
            </div>
            <div style="color:#666;font-size:11px;">
                95th percentile
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div style="background:#1e1e1e;padding:15px;border-radius:8px;border-left:4px solid #6f42c1;">
            <div style="color:#888;font-size:12px;">Avg Response Time</div>
            <div style="font-size:28px;font-weight:bold;color:#6f42c1;">
                {latest["avg_response_time_ms"]/1000:.1f}s
            </div>
            <div style="color:#666;font-size:11px;">
                mean latency
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Response time distribution
    st.subheader("Response Time Distribution")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Percentiles")
        percentiles = {
            "Min": latest["min_response_time_ms"],
            "P50 (Median)": latest["p50_response_time_ms"],
            "P95": latest["p95_response_time_ms"],
            "P99": latest["p99_response_time_ms"],
            "Max": latest["max_response_time_ms"],
        }

        for label, value in percentiles.items():
            pct = min(100, (value / latest["max_response_time_ms"]) * 100) if latest["max_response_time_ms"] > 0 else 0
            color = get_response_time_color(value)
            st.markdown(f"""
            <div style="margin:5px 0;">
                <div style="display:flex;justify-content:space-between;margin-bottom:2px;">
                    <span style="color:#888;">{label}</span>
                    <span style="color:{color};font-weight:bold;">{value/1000:.2f}s</span>
                </div>
                <div style="background:#333;border-radius:4px;height:8px;">
                    <div style="background:{color};width:{pct}%;height:100%;border-radius:4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown("#### Request Summary")
        st.markdown(f"""
        | Metric | Value |
        |--------|-------|
        | Total Requests | {latest["total_requests"]} |
        | Successful | {latest["successful_requests"]} |
        | Failed | {latest["failed_requests"]} |
        | Error Rate | {latest["error_rate_percent"]:.2f}% |
        | RPS Achieved | {latest["requests_per_second"]:.2f} |
        """)

    # Errors section
    if latest.get("errors"):
        st.divider()
        st.subheader("Errors")
        for error, count in sorted(latest["errors"].items(), key=lambda x: -x[1]):
            st.error(f"**[{count}x]** {error}")

    # History section
    if history_file.exists():
        st.divider()
        st.subheader("Test History")

        with open(history_file) as f:
            history = json.load(f)

        if history:
            # Create history table
            history_data = []
            for h in history[:10]:  # Show last 10
                history_data.append({
                    "Test ID": h["test_id"],
                    "Scenario": h["scenario"],
                    "Duration": f"{h['duration_seconds']}s",
                    "Requests": h["total_requests"],
                    "Success Rate": f"{100 - h['error_rate_percent']:.1f}%",
                    "RPS": f"{h['requests_per_second']:.1f}",
                    "P95": f"{h['p95_response_time_ms']/1000:.1f}s",
                })

            st.dataframe(history_data, use_container_width=True)

    # Instructions
    with st.expander("How to Run Load Tests"):
        st.markdown("""
        ### Running Load Tests

        ```bash
        # Activate virtual environment
        source venv/bin/activate

        # Run steady load test (default: 60 seconds)
        python loadtest/load_test.py --target https://api.zeroleaf.dev

        # Run longer test with specific RPS
        python loadtest/load_test.py --target https://api.zeroleaf.dev --duration 300 --max-rps 10

        # Run ramp-up test (gradual increase)
        python loadtest/load_test.py --target https://api.zeroleaf.dev --scenario ramp

        # Run spike test (periodic bursts)
        python loadtest/load_test.py --target https://api.zeroleaf.dev --scenario spike
        ```

        ### Scenarios

        | Scenario | Description |
        |----------|-------------|
        | **steady** | Constant load at max RPS |
        | **ramp** | Linear ramp from 10% to 100% |
        | **spike** | 30% baseline with 100% spikes |

        ### Limits

        - Maximum RPS: 33.33 (2000 requests/minute)
        - Results saved to `loadtest/results/`
        """)


if __name__ == "__main__":
    # Standalone mode for testing
    st.set_page_config(page_title="Load Test Dashboard", layout="wide")
    render_load_test_dashboard()
