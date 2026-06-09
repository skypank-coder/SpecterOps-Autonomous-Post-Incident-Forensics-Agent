"""
TraceArchaeologist — Agent 2 of 4.

Queries the Dynatrace MCP for traces, logs, metrics and topology in parallel,
compresses them into a compact evidence summary, and asks Gemini to
reconstruct a chronological incident timeline.
"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

from connectors import dynatrace_mcp, scenarios
from connectors.dynatrace_client import DynatraceClient, dynatrace_configured
from models.incident import (
    AgentStep,
    Incident,
    IncidentImpact,
    IncidentSeverity,
    TimelineEvent,
)
from utils.gemini_client import gemini_json


def _parse_json_safe(raw: str, fallback: dict) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        cleaned = raw.strip()
        if "```" in cleaned:
            lines = cleaned.split("\n")
            cleaned = "\n".join(l for l in lines if not l.startswith("```"))
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return fallback


def _summarize_traces(traces_payload: Dict[str, Any]) -> Dict[str, Any]:
    traces: List[Dict[str, Any]] = traces_payload.get("traces", [])
    if not traces:
        return {"count": 0, "error_count": 0, "error_rate_pct": 0,
                "p50_ms": 0, "p99_ms": 0, "sample_bad_span_tags": {}}

    durations = sorted(t.get("durationMs", 0) for t in traces)
    error_traces = [t for t in traces if t.get("status") == "ERROR"]

    def pct(p: float) -> float:
        idx = min(len(durations) - 1, int(len(durations) * p))
        return durations[idx]

    sample_bad_tags: Dict[str, Any] = {}
    for t in error_traces:
        for span in t.get("spans", []):
            tags = span.get("tags", {})
            if tags.get("db.index_hit") == "false" or "db.system" in tags:
                sample_bad_tags = tags
                break
        if sample_bad_tags:
            break

    count = len(traces)
    err = len(error_traces)
    return {
        "count": count,
        "error_count": err,
        "error_rate_pct": round(100 * err / count, 1) if count else 0,
        "p50_ms": pct(0.50),
        "p99_ms": pct(0.99),
        "sample_bad_span_tags": sample_bad_tags,
    }


def _summarize_metric(metric_payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        series = metric_payload["result"][0]["data"][0]["values"]
        series = [v for v in series if v is not None]
    except (KeyError, IndexError):
        series = []
    if not series:
        return {"min": 0, "max": 0, "latest": 0, "spike_ratio": 1.0}
    mn, mx, latest = min(series), max(series), series[-1]
    baseline = series[0] if series[0] else (mn or 1)
    spike = round(mx / baseline, 1) if baseline else 1.0
    return {"min": round(mn, 3), "max": round(mx, 3), "latest": round(latest, 3),
            "spike_ratio": spike}


async def run_trace_archaeologist(incident: Incident) -> Incident:
    classification = incident.raw_data.get("classification", {})
    scenario = incident.raw_data.get("scenario") or scenarios.get_scenario("db_index")
    primary = classification.get("primary_service") or scenario.get("primary_service") or (
        incident.affected_services[0] if incident.affected_services else "payment-service"
    )

    demo = os.getenv("DEMO_MODE", "true").lower() in ("1", "true", "yes")
    # Only a REAL Dynatrace problem (scenario id "dynatrace") hits the live API.
    # Built-in/custom scenarios are fictional and always use simulated telemetry,
    # so they stay rich even when the server runs in live (DEMO_MODE=false) mode.
    is_live_scenario = scenario.get("id") == "dynatrace"
    mcp_mode = is_live_scenario and (not demo) and dynatrace_mcp.mcp_configured()

    # When a real problem + MCP is available, gather evidence through the OFFICIAL
    # Dynatrace MCP server (list_problems / execute_dql / find_entity_by_name).
    mcp_evidence: Dict[str, Any] | None = None
    if mcp_mode:
        try:
            mcp_evidence = await dynatrace_mcp.gather_evidence(
                primary, incident.dynatrace_problem_id or ""
            )
        except Exception:
            mcp_evidence = None

    live_units = False
    if mcp_evidence is not None:
        incident.raw_data["mcp_evidence"] = mcp_evidence
        incident.raw_data["mcp_tools_used"] = mcp_evidence.get("tool_calls", [])
        live_units = True
        traces = {"traces": []}
        logs = {"results": []}
        topology = {"entities": []}
        rt_metrics = {"result": []}
        err_metrics = {"result": []}
    else:
        # Live REST only for a real Dynatrace problem; otherwise simulate.
        simulate = not (is_live_scenario and (not demo) and dynatrace_configured())
        client = DynatraceClient(
            problem_id=incident.dynatrace_problem_id, scenario=scenario, simulate=simulate
        )
        live_units = not client.demo
        entity_ids = scenario.get("dt_entity_ids")
        traces, logs, topology, rt_metrics, err_metrics = await asyncio.gather(
            client.get_traces(primary),
            client.get_logs(primary),
            client.get_topology(primary),
            client.get_metrics("builtin:service.response.time", primary, entity_ids=entity_ids),
            client.get_metrics("builtin:service.errors.total.rate", primary, entity_ids=entity_ids),
        )

    incident.raw_data["traces"] = traces
    incident.raw_data["logs"] = logs
    incident.raw_data["topology"] = topology
    incident.raw_data["metrics"] = {
        "builtin:service.response.time": rt_metrics,
        "builtin:service.errors.total.rate": err_metrics,
    }

    trace_summary = _summarize_traces(traces)
    metric_summary = {
        "builtin:service.response.time": _summarize_metric(rt_metrics),
        "builtin:service.errors.total.rate": _summarize_metric(err_metrics),
    }
    incident.raw_data["trace_summary"] = trace_summary
    incident.raw_data["metric_summary"] = metric_summary

    # Headline error rate and latency come from the metric series (the true
    # signal). The trace counts are a curated sample (healthy + degraded) used
    # to show the index-hit contrast, so they are reported separately rather
    # than as the headline error rate.
    rt = metric_summary["builtin:service.response.time"]
    err = metric_summary["builtin:service.errors.total.rate"]

    # The scenario carries a concrete remediation command when one applies.
    remediation = scenario.get("remediation")

    trace_count = trace_summary["count"]

    # Unit normalization. The simulated metrics use a 0–1 error fraction and
    # milliseconds; live Dynatrace returns failure rate as a percent (0–100) and
    # response time in MICROSECONDS. Normalize both to "%" and "ms".
    live = live_units

    def _err_pct(mx):
        if not mx:
            return None
        if mx <= 1.0:
            return round(mx * 100, 1)   # fraction -> percent (demo)
        if mx <= 100.0:
            return round(mx, 1)         # already percent (live)
        return None                     # implausible -> hide

    def _to_ms(v):
        if not v:
            return None
        ms = v / 1000.0 if live else v  # live response.time is microseconds
        return round(ms, 0) if 0 < ms <= 600000 else None

    error_rate = _err_pct(err["max"])
    p99 = _to_ms(rt["max"])
    baseline = _to_ms(rt["min"])
    spike = rt["spike_ratio"] if rt["max"] else None  # ratio is unitless

    # For live problems where the metric queries don't resolve, fall back to the
    # impact values parsed from the Dynatrace problem evidence.
    dt_impact = scenario.get("dt_impact") or {}
    if error_rate is None and dt_impact.get("error_rate_pct") is not None:
        error_rate = dt_impact["error_rate_pct"]
    if p99 is None and dt_impact.get("p99_latency_ms") is not None:
        p99 = dt_impact["p99_latency_ms"]

    incident.impact = IncidentImpact(
        error_rate_pct=error_rate,
        p99_latency_ms=p99,
        baseline_latency_ms=baseline,
        latency_spike_ratio=spike,
        affected_traces=trace_count or None,
        error_traces=trace_summary["error_count"] if trace_count else None,
        remediation_command=remediation,
    )

    log_entries = logs.get("results", [])[:8]
    compact_logs = [
        {"timestamp": l.get("timestamp"), "level": l.get("level"),
         "service": l.get("service"), "content": l.get("content")}
        for l in log_entries
    ]

    topo_summary = {}
    try:
        ent = topology["entities"][0]
        topo_summary = {
            "service": ent.get("displayName"),
            "calls": [c.get("name") for c in ent.get("calls", [])],
            "called_by": [c.get("name") for c in ent.get("calledBy", [])],
        }
    except (KeyError, IndexError):
        pass

    evidence = scenario.get("evidence") or []
    evidence_block = (
        "DYNATRACE PROBLEM EVIDENCE:\n" + "\n".join(f"- {e}" for e in evidence[:10]) + "\n\n"
        if evidence
        else ""
    )

    mcp_block = ""
    if mcp_evidence:
        mcp_block = (
            "LIVE DYNATRACE DATA — fetched via the official Dynatrace MCP server:\n"
            f"Error/Warn logs (execute_dql):\n{(mcp_evidence.get('logs') or '(none)')[:2500]}\n\n"
            f"Recent events (execute_dql):\n{(mcp_evidence.get('events') or '(none)')[:1200]}\n\n"
            f"Affected entity (find_entity_by_name):\n{(mcp_evidence.get('entity') or '(none)')[:800]}\n\n"
        )

    prompt = f"""You are an SRE reconstructing an incident timeline from observability data.

PRIMARY SERVICE: {primary}

{evidence_block}{mcp_block}TRACE SUMMARY:
{json.dumps(trace_summary, indent=2, default=str)}

METRIC SUMMARY (baseline -> spike):
{json.dumps(metric_summary, indent=2, default=str)}

SERVICE TOPOLOGY:
{json.dumps(topo_summary, indent=2, default=str)}

LOG ENTRIES (chronological, oldest first):
{json.dumps(compact_logs, indent=2, default=str)}

Reconstruct the chronological timeline of this incident. Respond with JSON:
{{
  "timeline": [
    {{
      "timestamp_offset_seconds_ago": 1380,
      "service": "service-name",
      "event_type": "metric_spike|error|cascade|database_issue",
      "description": "what happened",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "is_first_anomaly": false
    }}
  ],
  "first_anomaly_description": "string",
  "cascade_chain": ["service-a", "service-b"],
  "total_duration_minutes": 23
}}

Order events oldest-first (largest offset first). Mark the earliest true anomaly with is_first_anomaly=true."""

    offline = scenarios.offline_timeline(scenario)
    try:
        raw = await gemini_json(prompt)
        result = _parse_json_safe(raw, offline)
        if not result.get("timeline"):
            result = offline
    except Exception:
        result = offline

    incident.raw_data["timeline_analysis"] = result

    now = datetime.utcnow()
    events: List[TimelineEvent] = []
    for ev in result.get("timeline", []):
        offset = int(ev.get("timestamp_offset_seconds_ago", 0))
        try:
            sev = IncidentSeverity(ev.get("severity", "MEDIUM"))
        except ValueError:
            sev = IncidentSeverity.MEDIUM
        events.append(
            TimelineEvent(
                timestamp=now - timedelta(seconds=offset),
                service=ev.get("service", primary),
                event_type=ev.get("event_type", "error"),
                description=ev.get("description", ""),
                severity=sev,
                is_root_cause_candidate=bool(ev.get("is_first_anomaly", False)),
            )
        )

    events.sort(key=lambda e: e.timestamp)
    incident.timeline = events

    cascade = result.get("cascade_chain", [])
    if mcp_evidence is not None:
        tools = ", ".join(dict.fromkeys(mcp_evidence.get("tool_calls", []))) or "list_problems, execute_dql"
        action = f"Queried the Dynatrace MCP server (tools: {tools}) for {primary}"
        detail = f"Reconstructed {len(events)} timeline events from live Dynatrace data via MCP"
    else:
        action = f"Queried Dynatrace (traces/logs/metrics/topology) for {primary}"
        detail = (
            f"Reconstructed {len(events)} timeline events | "
            f"error rate {trace_summary['error_rate_pct']}% | "
            f"p99 {trace_summary['p99_ms']}ms | "
            f"cascade: {' -> '.join(cascade) if cascade else 'n/a'}"
        )

    incident.agent_steps.append(
        AgentStep(agent_name="TraceArchaeologist", action=action, result=detail)
    )
    return incident
