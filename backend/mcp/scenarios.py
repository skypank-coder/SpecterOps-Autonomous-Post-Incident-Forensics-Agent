"""
Scenario engine.

A scenario is a compact, JSON-serializable spec describing an incident: its
metadata, the shape of its telemetry (traces/logs/metrics/topology), and an
"offline analysis pack" the agents use when no Gemini key is configured.

This powers three things:
  * the built-in incident library (the demo picker),
  * fully custom incidents typed by a user,
  * deterministic, scenario-accurate offline output so the demo always completes.

When a real Gemini key is present the agents reason for themselves; the offline
pack is only the fallback.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

# --------------------------------------------------------------------------- #
# Built-in scenario library
# --------------------------------------------------------------------------- #
# Each scenario is a plain dict so it can ride inside the alert payload and be
# serialized to the dashboard / database without custom encoders.

SCENARIOS: Dict[str, Dict[str, Any]] = {
    "db_index": {
        "id": "db_index",
        "emoji": "🗄️",
        "name": "Missing database index",
        "title": "Response time degradation in payment-service",
        "severity": "CRITICAL",
        "category": "DATABASE_ISSUE",
        "primary_service": "payment-service",
        "services": ["payment-service", "order-service", "api-gateway"],
        "db": {"table": "payment_methods", "column": "user_id"},
        "metrics": {"rt_baseline": 120.0, "rt_peak": 4150.0,
                    "err_baseline": 0.02, "err_peak": 0.335, "cpu_peak": 89.0},
        "remediation": "CREATE INDEX CONCURRENTLY idx_payment_methods_user_id ON payment_methods (user_id);",
        "logs": [
            [1392, "WARN", "DB connection pool at 87% capacity (217/250 active connections)", "payment-service"],
            [1365, "WARN", "Slow query detected on payment_methods.user_id — missing index, full table scan took 847ms", "payment-service"],
            [1338, "ERROR", "Payment processing timeout after 3000ms waiting on postgresql", "payment-service"],
            [1315, "ERROR", "Circuit breaker OPEN — downstream postgresql p99=4200ms exceeds 3000ms budget", "payment-service"],
            [1290, "ERROR", "[order-service] payment-service returning 503, request queue depth 847", "order-service"],
            [1270, "ERROR", "[api-gateway] upstream timeout on /api/payment/*, circuit breaker triggered", "api-gateway"],
            [1130, "WARN", "[postgresql] Table payment_methods — missing index on user_id detected by query planner (seq scan, 847293 rows)", "postgresql"],
            [1080, "ERROR", "CRITICAL error rate 34%, p99 latency 4800ms across payment pipeline", "payment-service"],
        ],
        "analysis": {
            "classification_reasoning": "Response time and error-rate evidence on payment-service with downstream fan-out indicates a database-driven performance degradation.",
            "first_anomaly": "DB connection pool saturation on payment-service driven by un-indexed payment_methods.user_id lookups",
            "cascade_chain": ["postgresql", "payment-service", "order-service", "api-gateway"],
            "root_cause_category": "MISSING_DB_INDEX",
            "confidence_pct": 94,
            "root_cause_explanation": (
                "A missing index on payment_methods.user_id forced PostgreSQL into full table "
                "scans (847,293 rows), driving query p99 to 4.2s. payment-service exhausted its "
                "connection pool and tripped its circuit breaker, which cascaded 503s into "
                "order-service and api-gateway, producing a 34% error rate."
            ),
            "timeline": [
                [1392, "payment-service", "database_issue", "DB connection pool reached 87% capacity (217/250)", "MEDIUM", True],
                [1365, "postgresql", "database_issue", "Slow query on payment_methods.user_id — missing index, full table scan 847ms", "HIGH", False],
                [1338, "payment-service", "error", "Payment processing timeout after 3000ms waiting on postgresql", "HIGH", False],
                [1315, "payment-service", "cascade", "Circuit breaker OPEN — downstream postgresql p99=4200ms", "CRITICAL", False],
                [1290, "order-service", "cascade", "payment-service returning 503, request queue depth 847", "HIGH", False],
                [1270, "api-gateway", "cascade", "Upstream timeout on /api/payment/*, circuit breaker triggered", "HIGH", False],
                [1080, "payment-service", "metric_spike", "Error rate 34%, p99 latency 4800ms across payment pipeline", "CRITICAL", False],
            ],
            "nodes": [
                ["node-1", "postgresql", "Missing index on payment_methods.user_id (full table scan, 847293 rows)", 1365, True],
                ["node-2", "payment-service", "DB query timeout p99=4200ms, connection pool exhausted", 1338, False],
                ["node-3", "payment-service", "Circuit breaker OPEN to postgresql", 1315, False],
                ["node-4", "order-service", "Receiving 503 from payment-service, queue depth 847", 1290, False],
                ["node-5", "api-gateway", "Upstream timeout on /api/payment/*, 34% error rate", 1270, False],
            ],
            "edges": [
                ["node-1", "node-2", "caused", 0.96],
                ["node-2", "node-3", "triggered", 0.93],
                ["node-3", "node-4", "cascaded to", 0.90],
                ["node-4", "node-5", "propagated to", 0.88],
            ],
        },
    },

    "memory_leak": {
        "id": "memory_leak",
        "emoji": "🧠",
        "name": "JVM memory leak",
        "title": "Rising heap usage and GC pauses in catalog-service",
        "severity": "HIGH",
        "category": "MEMORY_LEAK",
        "primary_service": "catalog-service",
        "services": ["catalog-service", "search-service", "api-gateway"],
        "db": None,
        "metrics": {"rt_baseline": 90.0, "rt_peak": 3200.0,
                    "err_baseline": 0.01, "err_peak": 0.28, "cpu_peak": 97.0},
        "remediation": "Roll catalog-service pods and cap the unbounded ProductCache (set maxSize + TTL eviction).",
        "logs": [
            [1500, "WARN", "Heap usage 78% after deploy v3.2.0 — ProductCache holding 1.2M entries", "catalog-service"],
            [1440, "WARN", "G1 GC pause 1.8s, old-gen occupancy climbing steadily", "catalog-service"],
            [1380, "ERROR", "Full GC every 12s, request latency p99 2.4s", "catalog-service"],
            [1320, "ERROR", "java.lang.OutOfMemoryError: Java heap space in CatalogController", "catalog-service"],
            [1280, "ERROR", "[search-service] catalog-service health check failing, 503s on /catalog", "search-service"],
            [1240, "ERROR", "[api-gateway] catalog upstream unavailable, returning 502", "api-gateway"],
            [1120, "WARN", "Pod catalog-service-7b9 restarted (OOMKilled), 3rd restart in 10m", "catalog-service"],
            [1050, "ERROR", "Error rate 28% on catalog read path, GC overhead 64%", "catalog-service"],
        ],
        "analysis": {
            "classification_reasoning": "Steadily climbing heap, escalating GC pauses and OOMKilled restarts after a deploy indicate an unbounded in-memory cache leaking objects.",
            "first_anomaly": "Heap occupancy climbing right after deploy v3.2.0 due to an unbounded ProductCache",
            "cascade_chain": ["catalog-service", "search-service", "api-gateway"],
            "root_cause_category": "MEMORY_LEAK",
            "confidence_pct": 90,
            "root_cause_explanation": (
                "Deploy v3.2.0 introduced an unbounded ProductCache that retained ~1.2M entries, "
                "exhausting the JVM heap. Escalating G1 GC pauses and repeated OOMKilled restarts "
                "drove catalog-service latency past 2.4s, cascading 502/503s into search-service "
                "and api-gateway."
            ),
            "timeline": [
                [1500, "catalog-service", "memory", "Heap 78% after v3.2.0 — ProductCache 1.2M entries", "MEDIUM", True],
                [1440, "catalog-service", "memory", "G1 GC pause 1.8s, old-gen occupancy climbing", "HIGH", False],
                [1380, "catalog-service", "metric_spike", "Full GC every 12s, p99 latency 2.4s", "HIGH", False],
                [1320, "catalog-service", "error", "OutOfMemoryError: Java heap space", "CRITICAL", False],
                [1280, "search-service", "cascade", "catalog health checks failing, 503s on /catalog", "HIGH", False],
                [1240, "api-gateway", "cascade", "catalog upstream unavailable, 502s", "HIGH", False],
                [1050, "catalog-service", "metric_spike", "Error rate 28%, GC overhead 64%", "CRITICAL", False],
            ],
            "nodes": [
                ["node-1", "catalog-service", "Unbounded ProductCache leak (v3.2.0), 1.2M retained entries", 1500, True],
                ["node-2", "catalog-service", "JVM heap exhaustion, OutOfMemoryError", 1320, False],
                ["node-3", "catalog-service", "OOMKilled pod restarts, GC overhead 64%", 1120, False],
                ["node-4", "search-service", "503s on /catalog dependency", 1280, False],
                ["node-5", "api-gateway", "502 upstream unavailable, 28% error rate", 1240, False],
            ],
            "edges": [
                ["node-1", "node-2", "caused", 0.94],
                ["node-2", "node-3", "triggered", 0.92],
                ["node-2", "node-4", "cascaded to", 0.87],
                ["node-4", "node-5", "propagated to", 0.85],
            ],
        },
    },

    "deploy_regression": {
        "id": "deploy_regression",
        "emoji": "🚀",
        "name": "Bad deployment",
        "title": "Error spike after checkout-service v2.4.1 rollout",
        "severity": "CRITICAL",
        "category": "DEPLOYMENT",
        "primary_service": "checkout-service",
        "services": ["checkout-service", "order-service", "api-gateway"],
        "db": None,
        "metrics": {"rt_baseline": 110.0, "rt_peak": 2600.0,
                    "err_baseline": 0.015, "err_peak": 0.41, "cpu_peak": 72.0},
        "remediation": "Roll back checkout-service to v2.4.0 (kubectl rollout undo) and re-add the dropped TAX_SERVICE_URL env var.",
        "logs": [
            [1320, "INFO", "Deploy checkout-service v2.4.1 completed, 6/6 pods ready", "checkout-service"],
            [1305, "ERROR", "NullPointerException in TaxCalculator — TAX_SERVICE_URL is null", "checkout-service"],
            [1290, "ERROR", "500 on POST /checkout, 41% of requests failing post-deploy", "checkout-service"],
            [1270, "ERROR", "[order-service] checkout-service 500s, orders stuck in PENDING", "order-service"],
            [1255, "ERROR", "[api-gateway] /api/checkout 5xx ratio breached SLO (0.41)", "api-gateway"],
            [1230, "WARN", "Canary analysis skipped — deploy promoted directly to 100%", "checkout-service"],
            [1180, "ERROR", "Customer checkout success rate dropped to 59%", "checkout-service"],
            [1100, "ERROR", "Error budget for checkout-service exhausted for the month", "checkout-service"],
        ],
        "analysis": {
            "classification_reasoning": "Error rate jumps to 41% within seconds of a version rollout, with a deterministic NullPointerException — a classic bad-deploy regression.",
            "first_anomaly": "NullPointerException immediately after v2.4.1 because TAX_SERVICE_URL was dropped from the config",
            "cascade_chain": ["checkout-service", "order-service", "api-gateway"],
            "root_cause_category": "DEPLOYMENT",
            "confidence_pct": 96,
            "root_cause_explanation": (
                "Release v2.4.1 of checkout-service dropped the TAX_SERVICE_URL environment "
                "variable, causing a NullPointerException in TaxCalculator on every checkout. "
                "41% of requests returned 500 within seconds of promotion, leaving orders stuck "
                "in PENDING and breaching the api-gateway SLO."
            ),
            "timeline": [
                [1320, "checkout-service", "deploy", "v2.4.1 promoted directly to 100% (canary skipped)", "MEDIUM", True],
                [1305, "checkout-service", "error", "NullPointerException — TAX_SERVICE_URL is null", "CRITICAL", False],
                [1290, "checkout-service", "metric_spike", "500s on /checkout, 41% failing", "CRITICAL", False],
                [1270, "order-service", "cascade", "Orders stuck PENDING from checkout 500s", "HIGH", False],
                [1255, "api-gateway", "cascade", "/api/checkout 5xx ratio breached SLO", "HIGH", False],
                [1180, "checkout-service", "metric_spike", "Checkout success rate dropped to 59%", "CRITICAL", False],
            ],
            "nodes": [
                ["node-1", "checkout-service", "Deploy v2.4.1 dropped TAX_SERVICE_URL env var", 1320, True],
                ["node-2", "checkout-service", "NullPointerException in TaxCalculator", 1305, False],
                ["node-3", "checkout-service", "41% of /checkout returning 500", 1290, False],
                ["node-4", "order-service", "Orders stuck in PENDING", 1270, False],
                ["node-5", "api-gateway", "/api/checkout SLO breach (5xx 0.41)", 1255, False],
            ],
            "edges": [
                ["node-1", "node-2", "caused", 0.97],
                ["node-2", "node-3", "triggered", 0.95],
                ["node-3", "node-4", "cascaded to", 0.9],
                ["node-3", "node-5", "propagated to", 0.89],
            ],
        },
    },

    "dependency_outage": {
        "id": "dependency_outage",
        "emoji": "🔌",
        "name": "Third-party dependency outage",
        "title": "Elevated latency from Stripe API timeouts in billing-service",
        "severity": "HIGH",
        "category": "DEPENDENCY_FAILURE",
        "primary_service": "billing-service",
        "services": ["billing-service", "subscription-service", "api-gateway"],
        "db": None,
        "metrics": {"rt_baseline": 140.0, "rt_peak": 8000.0,
                    "err_baseline": 0.02, "err_peak": 0.22, "cpu_peak": 41.0},
        "remediation": "Enable the Stripe circuit breaker with a 2s timeout + fallback queue; retry charges asynchronously.",
        "logs": [
            [1400, "WARN", "Stripe API p95 latency rising: 1.2s (normal 220ms)", "billing-service"],
            [1350, "ERROR", "Stripe charge request timed out after 10000ms", "billing-service"],
            [1300, "ERROR", "No circuit breaker on Stripe client — threads blocked in WAITING", "billing-service"],
            [1260, "ERROR", "billing-service thread pool exhausted (200/200 busy)", "billing-service"],
            [1230, "ERROR", "[subscription-service] billing-service not responding, renewals failing", "subscription-service"],
            [1200, "ERROR", "[api-gateway] /api/billing p99 8.1s, 22% timeouts", "api-gateway"],
            [1150, "WARN", "Stripe status page: 'Elevated error rates on Charges API'", "billing-service"],
            [1080, "ERROR", "Subscription renewal backlog at 1,240 and growing", "subscription-service"],
        ],
        "analysis": {
            "classification_reasoning": "Latency to an external provider (Stripe) spikes while internal CPU stays low, and threads block waiting on it — an upstream dependency failure, not an internal bug.",
            "first_anomaly": "Stripe Charges API latency climbing well beyond its 220ms baseline with no client-side timeout",
            "cascade_chain": ["stripe-api", "billing-service", "subscription-service", "api-gateway"],
            "root_cause_category": "EXTERNAL_DEPENDENCY",
            "confidence_pct": 88,
            "root_cause_explanation": (
                "Stripe's Charges API degraded (10s timeouts). billing-service had no circuit "
                "breaker or timeout on the Stripe client, so request threads blocked until the "
                "pool was exhausted (200/200). That stalled subscription renewals and pushed "
                "api-gateway /api/billing p99 to 8.1s with 22% timeouts."
            ),
            "timeline": [
                [1400, "stripe-api", "dependency", "Stripe Charges API p95 1.2s (normal 220ms)", "MEDIUM", True],
                [1350, "billing-service", "error", "Stripe charge timed out after 10000ms", "HIGH", False],
                [1300, "billing-service", "error", "No circuit breaker — threads blocked WAITING", "HIGH", False],
                [1260, "billing-service", "metric_spike", "Thread pool exhausted (200/200)", "CRITICAL", False],
                [1230, "subscription-service", "cascade", "Renewals failing, billing unresponsive", "HIGH", False],
                [1200, "api-gateway", "cascade", "/api/billing p99 8.1s, 22% timeouts", "HIGH", False],
            ],
            "nodes": [
                ["node-1", "stripe-api", "External Stripe Charges API degradation (10s timeouts)", 1400, True],
                ["node-2", "billing-service", "No timeout/circuit breaker, threads block on Stripe", 1300, False],
                ["node-3", "billing-service", "Thread pool exhausted 200/200", 1260, False],
                ["node-4", "subscription-service", "Renewal backlog 1,240", 1230, False],
                ["node-5", "api-gateway", "/api/billing p99 8.1s, 22% timeouts", 1200, False],
            ],
            "edges": [
                ["node-1", "node-2", "caused", 0.9],
                ["node-2", "node-3", "triggered", 0.92],
                ["node-3", "node-4", "cascaded to", 0.86],
                ["node-3", "node-5", "propagated to", 0.84],
            ],
        },
    },
}

SCENARIO_ORDER = ["db_index", "memory_leak", "deploy_regression", "dependency_outage"]


def list_scenarios() -> List[Dict[str, Any]]:
    """Lightweight metadata for the dashboard picker."""
    out = []
    for sid in SCENARIO_ORDER:
        s = SCENARIOS[sid]
        out.append({
            "id": s["id"],
            "emoji": s["emoji"],
            "name": s["name"],
            "title": s["title"],
            "severity": s["severity"],
            "category": s["category"],
            "primary_service": s["primary_service"],
            "services": s["services"],
        })
    return out


def get_scenario(scenario_id: Optional[str]) -> Dict[str, Any]:
    return SCENARIOS.get(scenario_id or "db_index", SCENARIOS["db_index"])


# --------------------------------------------------------------------------- #
# Custom scenario builder
# --------------------------------------------------------------------------- #
def build_custom_scenario(
    title: str,
    description: str,
    services: Optional[List[str]] = None,
    severity: str = "HIGH",
) -> Dict[str, Any]:
    """Turn free-text user input into a runnable scenario spec."""
    services = [s.strip() for s in (services or []) if s.strip()] or ["app-service", "api-gateway"]
    primary = services[0]
    downstream = services[1] if len(services) > 1 else "api-gateway"
    desc = (description or title).strip()
    short = (desc[:140] + "…") if len(desc) > 140 else desc

    return {
        "id": "custom",
        "emoji": "✳️",
        "name": "Custom incident",
        "title": title or "Custom production incident",
        "severity": severity if severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW") else "HIGH",
        "category": "UNKNOWN",
        "primary_service": primary,
        "services": services,
        "db": None,
        "metrics": {"rt_baseline": 130.0, "rt_peak": 3000.0,
                    "err_baseline": 0.02, "err_peak": 0.24, "cpu_peak": 70.0},
        "remediation": None,
        "user_description": desc,
        "logs": [
            [1300, "WARN", f"Anomaly detected on {primary}: {short}", primary],
            [1260, "WARN", f"{primary} latency rising above baseline", primary],
            [1220, "ERROR", f"{primary} returning elevated error responses", primary],
            [1180, "ERROR", f"[{downstream}] degraded responses from {primary}", downstream],
            [1120, "ERROR", f"User-facing impact observed across {', '.join(services)}", primary],
            [1050, "ERROR", f"Error rate elevated on {primary}", primary],
        ],
        "analysis": {
            "classification_reasoning": f"User-reported incident on {primary}: {short}",
            "first_anomaly": f"Initial anomaly on {primary} — {short}",
            "cascade_chain": services,
            "root_cause_category": "OTHER",
            "confidence_pct": 72,
            "root_cause_explanation": (
                f"Based on the reported symptoms, the incident originates in {primary} "
                f"and degrades dependent services ({', '.join(services[1:]) or 'downstream consumers'}). "
                f"Reported context: {short}"
            ),
            "timeline": [
                [1300, primary, "error", f"Reported symptom: {short}", "HIGH", True],
                [1260, primary, "metric_spike", f"{primary} latency rising above baseline", "HIGH", False],
                [1180, downstream, "cascade", f"{downstream} degraded by {primary}", "HIGH", False],
                [1050, primary, "metric_spike", f"Error rate elevated on {primary}", "CRITICAL", False],
            ],
            "nodes": [
                ["node-1", primary, f"Root cause on {primary} — {short[:60]}", 1300, True],
                ["node-2", primary, f"{primary} error/latency degradation", 1180, False],
                ["node-3", downstream, f"{downstream} impacted downstream", 1050, False],
            ],
            "edges": [
                ["node-1", "node-2", "caused", 0.82],
                ["node-2", "node-3", "cascaded to", 0.78],
            ],
        },
    }


_DT_SEVERITY = {
    "AVAILABILITY": "CRITICAL",
    "ERROR": "CRITICAL",
    "PERFORMANCE": "HIGH",
    "RESOURCE_CONTENTION": "HIGH",
    "CUSTOM_ALERT": "MEDIUM",
    "MONITORING_UNAVAILABLE": "MEDIUM",
}


def _parse_impact(strings: List[str]) -> Tuple[Optional[float], Optional[float]]:
    """
    Heuristically pull an error-rate % and a latency (ms) out of evidence text.

    Values are range-validated — an error rate must be 0–100% and a latency must
    be plausible — so a misparse shows nothing rather than a nonsense number.
    """
    err: Optional[float] = None
    p99: Optional[float] = None
    for s in strings:
        low = s.lower()
        m = re.search(r"(\d+(?:\.\d+)?)\s*%", s)
        if m and any(k in low for k in ("error", "failure", "rate")):
            v = float(m.group(1))
            if 0 < v <= 100:
                err = v
        m2 = re.search(r"(\d+(?:\.\d+)?)\s*(ms|s)\b", low)
        if m2 and any(k in low for k in ("time", "latency", "response", "duration")):
            v = float(m2.group(1))
            if m2.group(2) == "s":
                v *= 1000
            if 0 < v <= 600000:  # up to 10 minutes
                p99 = v
    return err, p99


def build_dynatrace_scenario(problem: Dict[str, Any]) -> Dict[str, Any]:
    """Build a rich, real-data scenario from a live Dynatrace problem object."""
    title = problem.get("title", "Dynatrace problem")
    severity = _DT_SEVERITY.get(problem.get("severityLevel", ""), "HIGH")

    affected = problem.get("affectedEntities", []) or []
    services = [e.get("name", "") for e in affected if e.get("name")] or ["affected-service"]
    impacted = problem.get("impactedEntities", []) or []
    primary = (impacted[0].get("name") if impacted else None) or services[0]
    entity_ids = [
        (e.get("entityId") or {}).get("id")
        for e in affected
        if (e.get("entityId") or {}).get("id")
    ]

    details = (problem.get("evidenceDetails") or {}).get("details", []) or []
    evidence = [d.get("displayName", "") for d in details if d.get("displayName")]
    evidence = list(dict.fromkeys(evidence))  # de-dupe, preserve order
    if not evidence:
        evidence = [title]

    err, p99 = _parse_impact(evidence + [title])

    ev = evidence[:6]
    n = len(ev)
    start = 1380
    step = max(60, (start - 120) // max(1, n))
    timeline = []
    logs = []
    for i, d in enumerate(ev):
        off = start - i * step
        timeline.append([off, primary, "evidence", d, severity, i == 0])
        logs.append([off, "ERROR" if severity in ("CRITICAL", "HIGH") else "WARN", d, primary])

    others = [s for s in services if s != primary][:3]
    nodes = [["node-1", primary, evidence[0], start, True]]
    edges = []
    prev = "node-1"
    for j, s in enumerate(others, start=2):
        nid = f"node-{j}"
        nodes.append([nid, s, f"Impacted downstream by {primary}", start - (j - 1) * step, False])
        edges.append([prev, nid, "cascaded to", 0.85])
        prev = nid

    explanation = (
        f"Dynatrace flagged '{title}'. The root cause is localized to {primary}"
        + (f", cascading to {', '.join(others)}" if others else "")
        + ". Key evidence: "
        + ("; ".join(evidence[:3]) if evidence else "see problem details")
        + "."
    )

    return {
        "id": "dynatrace",
        "emoji": "🟣",
        "name": "Live Dynatrace problem",
        "title": title,
        "severity": severity,
        "category": "OTHER",
        "primary_service": primary,
        "services": services,
        "db": None,
        "metrics": {
            "rt_baseline": 120.0,
            "rt_peak": p99 or 3000.0,
            "err_baseline": 0.02,
            "err_peak": (err / 100.0) if err else 0.2,
            "cpu_peak": 70.0,
        },
        "remediation": None,
        "evidence": evidence,
        "dt_entity_ids": entity_ids,
        "dt_impact": {"error_rate_pct": err, "p99_latency_ms": p99},
        "logs": logs,
        "analysis": {
            "classification_reasoning": f"Dynatrace problem on {primary}: {title}",
            "first_anomaly": evidence[0],
            "cascade_chain": [primary] + others,
            "root_cause_category": "OTHER",
            "confidence_pct": 88,
            "root_cause_explanation": explanation,
            "timeline": timeline,
            "nodes": nodes,
            "edges": edges,
        },
    }


# --------------------------------------------------------------------------- #
# Telemetry generators (Dynatrace-shaped)
# --------------------------------------------------------------------------- #
def _iso(dt: datetime) -> str:
    return dt.isoformat() + "Z"


def gen_traces(scenario: Dict[str, Any]) -> Dict[str, Any]:
    base = datetime.utcnow()
    service = scenario["primary_service"]
    db = scenario.get("db")
    peak = scenario["metrics"]["rt_peak"]
    traces: List[Dict[str, Any]] = []

    for i in range(50):
        healthy = i < 15
        if healthy:
            duration = 110 + (i * 3) % 41
            status = "OK"
            http_code = "200"
        else:
            duration = int(peak) + (i * 37) % 900
            status = "ERROR"
            http_code = "503" if not db else "503"

        spans = [{
            "spanId": f"span-{i:04d}-svc",
            "name": f"{service} POST /api/request",
            "kind": "SERVER",
            "durationMs": duration,
            "status": status,
            "tags": {
                "service.name": service,
                "http.method": "POST",
                "http.route": "/api/request",
                "http.status_code": http_code,
            },
        }]

        if db:
            spans.append({
                "spanId": f"span-{i:04d}-db",
                "name": f"postgresql.query SELECT {db['table']}",
                "kind": "CLIENT",
                "durationMs": max(1, duration - 120),
                "status": status,
                "tags": {
                    "db.system": "postgresql",
                    "db.statement": f"SELECT * FROM {db['table']} WHERE {db['column']} = $1",
                    "db.table": db["table"],
                    "db.index_hit": "true" if healthy else "false",
                    "db.rows_examined": str(10 + (i % 6)) if healthy else "847293",
                    "db.rows_returned": "1",
                },
            })

        traces.append({
            "traceId": f"trace-{i:04d}-{service}",
            "status": status,
            "durationMs": duration,
            "startTime": _iso(base - timedelta(seconds=(50 - i) * 26)),
            "spans": spans,
        })

    return {
        "service": service,
        "totalCount": len(traces),
        "errorCount": sum(1 for t in traces if t["status"] == "ERROR"),
        "traces": traces,
    }


def gen_logs(scenario: Dict[str, Any]) -> Dict[str, Any]:
    base = datetime.utcnow()
    results = []
    for offset, level, content, source in scenario["logs"]:
        results.append({
            "timestamp": _iso(base - timedelta(seconds=offset)),
            "level": level,
            "status": level,
            "content": content,
            "service": source,
            "loglevel": level,
        })
    results.sort(key=lambda r: r["timestamp"])
    return {"service": scenario["primary_service"], "totalCount": len(results), "results": results}


def gen_metrics(scenario: Dict[str, Any], metric_key: str) -> Dict[str, Any]:
    base = datetime.utcnow()
    m = scenario["metrics"]
    timestamps = [int((base - timedelta(seconds=(30 - i) * 46)).timestamp() * 1000) for i in range(30)]

    if metric_key == "builtin:service.response.time":
        values = [m["rt_baseline"] + (i % 4) * 5 for i in range(15)] + \
                 [m["rt_peak"] + (i % 5) * 25 for i in range(15)]
    elif metric_key == "builtin:service.errors.total.rate":
        values = [m["err_baseline"] + (i % 3) * 0.005 for i in range(18)] + \
                 [m["err_peak"] + (i % 3) * 0.002 for i in range(12)]
    elif metric_key == "builtin:host.cpu.usage":
        base_cpu = max(20.0, m["cpu_peak"] - 55)
        values = [base_cpu + (i % 5) * 2 for i in range(15)] + \
                 [m["cpu_peak"] + (i % 4) for i in range(15)]
    else:
        values = [50.0 for _ in range(30)]

    values = [round(v, 4) for v in values]
    return {
        "totalCount": 1,
        "result": [{
            "metricId": metric_key,
            "data": [{
                "dimensions": [scenario["primary_service"]],
                "dimensionMap": {"dt.entity.service": scenario["primary_service"]},
                "timestamps": timestamps,
                "values": values,
            }],
        }],
        "datapoints": [[timestamps[i], values[i]] for i in range(30)],
    }


def gen_topology(scenario: Dict[str, Any]) -> Dict[str, Any]:
    services = scenario["services"]
    primary = scenario["primary_service"]
    db = scenario.get("db")
    calls = []
    if db:
        calls.append({"name": "postgresql", "type": "RELATIONAL_DATABASE", "entityId": "DATABASE-PG01"})
    calls.append({"name": "redis", "type": "SERVICE", "entityId": "SERVICE-REDIS"})
    called_by = [
        {"name": s, "type": "SERVICE", "entityId": f"SERVICE-{s[:4].upper()}"}
        for s in services if s != primary
    ]
    return {
        "totalCount": 1,
        "entities": [{
            "entityId": "SERVICE-PRIMARY",
            "displayName": primary,
            "type": "SERVICE",
            "calls": calls,
            "calledBy": called_by,
        }],
    }


# --------------------------------------------------------------------------- #
# Offline analysis packs (used when Gemini is unavailable)
# --------------------------------------------------------------------------- #
def offline_classification(scenario: Dict[str, Any]) -> Dict[str, Any]:
    a = scenario["analysis"]
    return {
        "primary_service": scenario["primary_service"],
        "title": scenario["title"],
        "severity": scenario["severity"],
        "affected_services": scenario["services"],
        "category": scenario["category"],
        "metrics_to_investigate": ["builtin:service.response.time", "builtin:service.errors.total.rate"],
        "classification_reasoning": a["classification_reasoning"],
    }


def offline_timeline(scenario: Dict[str, Any]) -> Dict[str, Any]:
    a = scenario["analysis"]
    return {
        "timeline": [
            {"timestamp_offset_seconds_ago": t[0], "service": t[1], "event_type": t[2],
             "description": t[3], "severity": t[4], "is_first_anomaly": t[5]}
            for t in a["timeline"]
        ],
        "first_anomaly_description": a["first_anomaly"],
        "cascade_chain": a["cascade_chain"],
        "total_duration_minutes": 23,
    }


def offline_graph(scenario: Dict[str, Any]) -> Dict[str, Any]:
    a = scenario["analysis"]
    return {
        "root_cause_node_id": a["nodes"][0][0] if a["nodes"] else None,
        "root_cause_explanation": a["root_cause_explanation"],
        "root_cause_category": a["root_cause_category"],
        "confidence_pct": a["confidence_pct"],
        "nodes": [
            {"id": n[0], "service": n[1], "event": n[2],
             "timestamp_offset_seconds_ago": n[3], "is_root_cause": n[4]}
            for n in a["nodes"]
        ],
        "edges": [
            {"source": e[0], "target": e[1], "relationship": e[2], "confidence": e[3]}
            for e in a["edges"]
        ],
    }


def offline_postmortem(scenario: Dict[str, Any], incident) -> str:
    """Assemble a complete Markdown post-mortem from the scenario + incident."""
    a = scenario["analysis"]
    services = ", ".join(scenario["services"])
    confidence = incident.root_cause_confidence or a["confidence_pct"]
    summary = incident.root_cause_summary or a["root_cause_explanation"]

    timeline_rows = "\n".join(
        f"| {e.timestamp.strftime('%H:%M:%S')} | {e.service} | {e.description} | {e.severity.value} |"
        for e in incident.timeline
    ) or "| — | — | No timeline reconstructed | — |"

    cascade = " → ".join(a["cascade_chain"])
    remediation = scenario.get("remediation")
    remediation_step = (
        f"1. Apply the primary fix: `{remediation}`"
        if remediation
        else "1. Mitigate the root cause identified above (roll back, scale, or patch the failing component)."
    )

    return f"""## Executive Summary

A **{incident.severity.value}** incident affecting **{services}** was detected and
diagnosed autonomously by SpecterOps with **{confidence}% confidence**. {summary}

## Impact

User-facing requests across {services} experienced elevated errors and latency.
The blast radius followed the dependency chain: {cascade}.

## Root Cause

{summary}

## Timeline

| Time | Service | Event | Severity |
| --- | --- | --- | --- |
{timeline_rows}

## Causal Chain

{cascade}

## Detection & Response

Dynatrace raised problem **{incident.dynatrace_problem_id or 'P-DEMO'}**. SpecterOps
autonomously pulled traces, logs, metrics and topology, reconstructed the timeline,
and isolated the root cause in under 60 seconds.

## Immediate Remediation Steps

{remediation_step}
2. Confirm error rate and p99 latency return to baseline.
3. Verify dependent services recover and drain any backlog/queues.

## Action Items

| Item | Owner | Priority | Due Date |
| --- | --- | --- | --- |
| Remediate root cause ({a['root_cause_category']}) | Owning Team | P0 | Immediate |
| Add a targeted alert for this failure mode | Platform/SRE | P1 | +3 days |
| Add a regression guard to CI | Eng Team | P2 | +1 week |
| Review blast-radius / bulkheads for {scenario['primary_service']} | Architecture | P2 | +1 week |

## Lessons Learned

A localized failure in **{scenario['primary_service']}** was able to cascade across
{len(scenario['services'])} services. Faster isolation and tighter bulkheads would
have contained the blast radius.

## Prevention Measures

- Add automated detection for this specific failure signature.
- Strengthen circuit breakers and timeouts between {services}.
- Add regression tests and progressive-delivery guards.
- Alert on leading indicators, not just user-facing symptoms.
"""
