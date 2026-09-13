"""
Solution: SLO Reporter — Queries Prometheus and reports SLO status

Run:
  pip install requests
  python slo_reporter.py
"""

import sys
import requests

PROMETHEUS_URL = "http://localhost:9090"

SLOS = {
    "success_rate": {
        "target": 99.5,
        "unit": "%",
        "higher_is_better": True,
    },
    "p99_latency_ms": {
        "target": 500,
        "unit": "ms",
        "higher_is_better": False,
    },
}


def query_prometheus(promql: str) -> float | None:
    """Execute a PromQL instant query and return the scalar result."""
    try:
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": promql},
            timeout=5,
        )
        data = response.json()
        results = data.get("data", {}).get("result", [])
        if not results:
            return None
        return float(results[0]["value"][1])
    except Exception as e:
        print(f"  ⚠️  Prometheus query failed: {e}")
        return None


def get_metrics() -> dict:
    """Fetch all required metrics from Prometheus."""
    # Total requests in last 30 minutes
    total = query_prometheus('sum(increase(http_requests_total[30m]))')
    
    # Error requests (5xx) in last 30 minutes
    errors = query_prometheus('sum(increase(http_requests_total{http_status=~"5.."}[30m]))')
    
    # p99 latency (in seconds, we convert to ms)
    p99_seconds = query_prometheus(
        'histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))'
    )

    success_rate = None
    if total is not None and total > 0:
        errors = errors or 0
        success_rate = (total - errors) / total * 100

    p99_ms = p99_seconds * 1000 if p99_seconds is not None else None

    return {
        "total_requests": total,
        "error_requests": errors,
        "success_rate": success_rate,
        "p99_latency_ms": p99_ms,
    }


def calculate_error_budget(current_rate: float, slo_target: float) -> float:
    """
    Error budget consumed as a percentage.
    
    If SLO = 99.5% and current = 99.73%:
      Allowed error rate = 0.5%
      Actual error rate  = 0.27%
      Budget consumed    = 0.27 / 0.5 * 100 = 54%
    """
    allowed_error_rate = 100 - slo_target
    actual_error_rate = 100 - current_rate
    if allowed_error_rate == 0:
        return 100.0
    return min(100.0, (actual_error_rate / allowed_error_rate) * 100)


def print_report(metrics: dict) -> bool:
    """Print the SLO report. Returns True if all SLOs are met."""
    print()
    print("═" * 47)
    print("  Orders API — SLO Report (Last 30 minutes)")
    print("═" * 47)
    print()

    all_ok = True
    recommendations = []

    # Success Rate
    success_rate = metrics.get("success_rate")
    if success_rate is not None:
        target = SLOS["success_rate"]["target"]
        ok = success_rate >= target
        if not ok:
            all_ok = False
            recommendations.append("Investigate elevated error rate immediately.")
        
        budget_consumed = calculate_error_budget(success_rate, target)
        status_icon = "✅" if ok else "❌"
        budget_icon = "🟢" if budget_consumed < 50 else ("🟡" if budget_consumed < 80 else "🔴")

        print(f"  {status_icon} Success Rate:     {success_rate:.2f}%    (SLO: {target}%)")
        print(f"  {budget_icon}   Error Budget:     {budget_consumed:.0f}% consumed")
        breach_note = "" if ok else "  ← SLO BREACH!"
        print(f"{breach_note}")
    else:
        print("  ⚠️  Success Rate: No data (is the service running?)")

    print()

    # p99 Latency
    p99_ms = metrics.get("p99_latency_ms")
    if p99_ms is not None:
        target = SLOS["p99_latency_ms"]["target"]
        ok = p99_ms <= target
        if not ok:
            all_ok = False
            recommendations.append(f"Investigate latency — p99 ({p99_ms:.0f}ms) is above {target}ms target.")
        
        status_icon = "✅" if ok else "⚠️ "
        breach_note = "" if ok else "  ← SLO BREACH!"
        print(f"  {status_icon} p99 Latency:      {p99_ms:.0f}ms      (SLO: <{target}ms){breach_note}")
    else:
        print("  ⚠️  p99 Latency: No data")

    print()
    if recommendations:
        print("  Recommendations:")
        for rec in recommendations:
            print(f"    → {rec}")
        print()

    overall = "✅ All SLOs MET" if all_ok else "❌ SLO BREACHES DETECTED"
    print(f"  Overall: {overall}")
    print("═" * 47)
    print()
    return all_ok


if __name__ == "__main__":
    print("Querying Prometheus...")
    metrics = get_metrics()
    all_slos_met = print_report(metrics)
    sys.exit(0 if all_slos_met else 1)
