"""
End-to-end and unit tests for the SpecterOps pipeline.

These run with DEMO_MODE on and no Gemini key, exercising the offline fallback
path so they're deterministic in CI. They assert the same guarantees the
hackathon verification checks for: a complete incident with 4 agent steps, a
populated timeline, a causal graph, impact metrics, timing, and a real
post-mortem.
"""
import os
import uuid

import pytest

os.environ.setdefault("DEMO_MODE", "true")

from agents.orchestrator import forget_incident, process_incident
from mcp import mock_data
from mcp.dynatrace_client import DynatraceClient
from models.incident import IncidentStatus


DEMO_ALERT = {
    "problemId": "P-DEMO-001",
    "title": "Response time degradation in payment-service",
    "affectedEntities": [
        {"entityId": {"id": "S1", "type": "SERVICE"}, "name": "payment-service"},
        {"entityId": {"id": "S2", "type": "SERVICE"}, "name": "order-service"},
        {"entityId": {"id": "S3", "type": "SERVICE"}, "name": "api-gateway"},
    ],
}


@pytest.mark.asyncio
async def test_full_pipeline_completes():
    incident_id = str(uuid.uuid4())
    try:
        inc = await process_incident(incident_id, DEMO_ALERT)

        assert inc.status == IncidentStatus.COMPLETE
        assert len(inc.agent_steps) == 4
        agent_names = [s.agent_name for s in inc.agent_steps]
        assert agent_names == [
            "SentinelAgent",
            "TraceArchaeologist",
            "BlameMapper",
            "NarratorAgent",
        ]
        assert len(inc.timeline) >= 5
        assert inc.causal_graph is not None
        assert len(inc.causal_graph.nodes) >= 2
        assert any(n.is_root_cause for n in inc.causal_graph.nodes)
        assert inc.postmortem and len(inc.postmortem) > 500
    finally:
        forget_incident(incident_id)


@pytest.mark.asyncio
async def test_pipeline_sets_impact_and_timing():
    incident_id = str(uuid.uuid4())
    try:
        inc = await process_incident(incident_id, DEMO_ALERT)

        assert inc.impact is not None
        assert inc.impact.error_rate_pct and inc.impact.error_rate_pct > 0
        assert inc.impact.p99_latency_ms and inc.impact.p99_latency_ms > 0
        assert inc.impact.remediation_command  # DB index case
        assert inc.analysis_duration_seconds is not None
        assert inc.analysis_duration_seconds >= 0
        assert inc.root_cause_confidence and inc.root_cause_confidence > 0
    finally:
        forget_incident(incident_id)


@pytest.mark.asyncio
async def test_timeline_is_chronological():
    incident_id = str(uuid.uuid4())
    try:
        inc = await process_incident(incident_id, DEMO_ALERT)
        times = [e.timestamp for e in inc.timeline]
        assert times == sorted(times)
    finally:
        forget_incident(incident_id)


@pytest.mark.asyncio
async def test_postmortem_has_required_sections():
    incident_id = str(uuid.uuid4())
    try:
        inc = await process_incident(incident_id, DEMO_ALERT)
        pm = inc.postmortem
        for header in ["## Executive Summary", "## Root Cause", "## Timeline", "## Action Items"]:
            assert header in pm, f"missing section: {header}"
    finally:
        forget_incident(incident_id)


@pytest.mark.asyncio
async def test_dynatrace_client_demo_mode():
    client = DynatraceClient()
    traces = await client.get_traces("payment-service")
    assert traces["totalCount"] == 50
    assert traces["errorCount"] == 35  # 15 healthy + 35 degraded

    logs = await client.get_logs("payment-service")
    assert len(logs["results"]) == 8

    metrics = await client.get_metrics("builtin:service.response.time", "payment-service")
    values = metrics["result"][0]["data"][0]["values"]
    assert len(values) == 30
    assert max(values) > 4000  # spike present
    assert min(values) < 200   # healthy baseline present


def test_mock_traces_split():
    payload = mock_data.mock_traces("payment-service")
    ok = [t for t in payload["traces"] if t["status"] == "OK"]
    err = [t for t in payload["traces"] if t["status"] == "ERROR"]
    assert len(ok) == 15
    assert len(err) == 35
    # Degraded traces must show the missing-index signal.
    for t in err:
        db_span = next(s for s in t["spans"] if s["tags"].get("db.system") == "postgresql")
        assert db_span["tags"]["db.index_hit"] == "false"
        assert db_span["tags"]["db.rows_examined"] == "847293"


def test_mock_logs_chronological():
    logs = mock_data.mock_logs("payment-service")["results"]
    ts = [l["timestamp"] for l in logs]
    assert ts == sorted(ts)
    assert len(logs) == 8
