"""Incident REST endpoints: list, fetch, demo/scenario trigger, custom trigger, delete."""
from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.orchestrator import (
    forget_incident,
    get_all_incidents,
    get_incident,
    process_incident,
)
from connectors import dynatrace_mcp, scenarios
from connectors.dynatrace_client import DynatraceClient, dynatrace_configured

router = APIRouter(prefix="/api/incidents", tags=["incidents"])

_DT_SEVERITY = {
    "AVAILABILITY": "CRITICAL",
    "ERROR": "CRITICAL",
    "PERFORMANCE": "HIGH",
    "RESOURCE_CONTENTION": "HIGH",
}


def _demo_mode() -> bool:
    return os.getenv("DEMO_MODE", "true").lower() in ("1", "true", "yes")


class TriggerRequest(BaseModel):
    scenario_id: Optional[str] = "db_index"
    owner: Optional[str] = None
    problem_id: Optional[str] = None  # specific Dynatrace problem to investigate


class CustomIncidentRequest(BaseModel):
    title: str
    description: str = ""
    services: List[str] = []
    severity: str = "HIGH"
    owner: Optional[str] = None


def _alert_from_scenario(scenario: dict, owner: Optional[str]) -> dict:
    return {
        "problemId": f"P-{scenario['id'].upper()}-{uuid.uuid4().hex[:6]}",
        "title": scenario["title"],
        "severityLevel": "PERFORMANCE",
        "status": "OPEN",
        "startTime": (datetime.utcnow() - timedelta(minutes=23)).isoformat() + "Z",
        "affectedEntities": [
            {"entityId": {"id": f"SERVICE-{i}", "type": "SERVICE"}, "name": s}
            for i, s in enumerate(scenario["services"])
        ],
        "scenario": scenario,
        "owner": owner,
    }


@router.get("/")
async def list_incidents(owner: Optional[str] = None):
    return [i.model_dump(mode="json") for i in get_all_incidents(owner=owner)]


@router.get("/{incident_id}")
async def fetch_incident(incident_id: str):
    incident = get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident.model_dump(mode="json")


@router.post("/demo/trigger")
async def trigger_demo(body: Optional[TriggerRequest] = None):
    body = body or TriggerRequest()
    scenario = scenarios.get_scenario(body.scenario_id)
    incident_id = str(uuid.uuid4())
    alert = _alert_from_scenario(scenario, body.owner)
    asyncio.create_task(process_incident(incident_id, alert))
    return {
        "incident_id": incident_id,
        "scenario_id": scenario["id"],
        "message": "Incident triggered — connect to the SSE stream to watch the analysis",
        "status": "analysis_started",
    }


@router.post("/custom/trigger")
async def trigger_custom(body: CustomIncidentRequest):
    if not body.title.strip():
        raise HTTPException(status_code=400, detail="title is required")
    scenario = scenarios.build_custom_scenario(
        title=body.title,
        description=body.description,
        services=body.services,
        severity=body.severity,
    )
    incident_id = str(uuid.uuid4())
    alert = _alert_from_scenario(scenario, body.owner)
    asyncio.create_task(process_incident(incident_id, alert))
    return {
        "incident_id": incident_id,
        "scenario_id": "custom",
        "message": "Custom incident triggered",
        "status": "analysis_started",
    }


@router.post("/dynatrace/trigger")
async def trigger_from_dynatrace(body: Optional[TriggerRequest] = None):
    """Pull the most recent OPEN problem from the live Dynatrace tenant and analyze it."""
    body = body or TriggerRequest()
    if _demo_mode() or not (dynatrace_mcp.mcp_configured() or dynatrace_configured()):
        raise HTTPException(
            status_code=400,
            detail="Live Dynatrace is not connected. Set DT_ENVIRONMENT (MCP) or DYNATRACE_URL/TOKEN, and DEMO_MODE=false.",
        )

    # Preferred path: the official Dynatrace MCP server.
    if dynatrace_mcp.mcp_configured():
        try:
            problems = await dynatrace_mcp.list_problems(status="ALL", timeframe="24h", limit=50)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Dynatrace MCP error: {exc}")
        if not problems:
            raise HTTPException(status_code=404, detail="No problems found via Dynatrace MCP.")
        chosen = None
        if body.problem_id:
            chosen = next(
                (p for p in problems if body.problem_id in (p["id"], p["display_id"])), None
            )
        chosen = chosen or problems[0]
        scenario = scenarios.build_custom_scenario(
            title=chosen["title"],
            description=f"Dynatrace {chosen['category']} problem (status {chosen['status']})",
            services=[],
            severity=chosen["severity"],
        )
        scenario["id"] = "dynatrace"
        scenario["emoji"] = "🟣"
        scenario["name"] = "Live Dynatrace problem (MCP)"
        incident_id = str(uuid.uuid4())
        alert = _alert_from_scenario(scenario, body.owner)
        alert["problemId"] = chosen["id"]
        asyncio.create_task(process_incident(incident_id, alert))
        return {
            "incident_id": incident_id,
            "scenario_id": "dynatrace",
            "problem_id": chosen["id"],
            "via": "mcp",
            "message": "Live Dynatrace problem pulled via MCP — analysis started",
            "status": "analysis_started",
        }

    client = DynatraceClient()

    # A specific problem was chosen from the picker, or fall back to the latest.
    if body.problem_id:
        try:
            full = await client.get_problem_by_id(body.problem_id)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Dynatrace API error: {exc}")
        if not full or not full.get("title"):
            raise HTTPException(status_code=404, detail="That Dynatrace problem was not found.")
        problem = full
        problem_id = body.problem_id
    else:
        try:
            data = await client.get_open_problems()
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Dynatrace API error: {exc}")
        problems = data.get("problems", [])
        if not problems:
            raise HTTPException(status_code=404, detail="No open problems found in Dynatrace.")
        problem = problems[0]
        problem_id = problem.get("problemId") or problem.get("displayId")
        full = await client.get_problem_by_id(problem_id) if problem_id else {}

    scenario = scenarios.build_dynatrace_scenario(full or problem)

    incident_id = str(uuid.uuid4())
    alert = _alert_from_scenario(scenario, body.owner)
    alert["problemId"] = problem_id or alert["problemId"]
    asyncio.create_task(process_incident(incident_id, alert))
    return {
        "incident_id": incident_id,
        "scenario_id": "dynatrace",
        "problem_id": alert["problemId"],
        "message": "Live Dynatrace problem pulled — analysis started",
        "status": "analysis_started",
    }


@router.post("/{incident_id}/share/slack")
async def share_to_slack(incident_id: str):
    """Post the incident summary + remediation to a Slack incoming webhook."""
    webhook = os.getenv("SLACK_WEBHOOK_URL", "").strip()
    if not webhook or webhook.startswith("https://hooks.slack.com/services/your"):
        raise HTTPException(
            status_code=400,
            detail="Slack is not connected. Set SLACK_WEBHOOK_URL in the backend environment.",
        )
    incident = get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    impact = incident.impact
    fix = impact.remediation_command if impact and impact.remediation_command else "See post-mortem."
    lines = [
        f":ghost: *SpecterOps post-mortem* — *{incident.title}*",
        f"*Severity:* {incident.severity.value}   *Confidence:* {incident.root_cause_confidence or '—'}%   "
        f"*Services:* {', '.join(incident.affected_services)}",
        "",
        f"*Root cause:* {incident.root_cause_summary or '—'}",
        "",
        f"*Immediate fix:*\n```{fix}```",
    ]
    payload = {"text": "\n".join(lines)}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(webhook, json=payload)
            resp.raise_for_status()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Slack delivery failed: {exc}")

    return {"delivered": True}


@router.post("/{incident_id}/dynatrace/comment")
async def push_rca_to_dynatrace(incident_id: str):
    """Close the loop: post SpecterOps' root-cause analysis back onto the Dynatrace problem."""
    incident = get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    if _demo_mode() or not dynatrace_configured():
        raise HTTPException(
            status_code=400,
            detail="Live Dynatrace is not connected. Set DYNATRACE_URL, DYNATRACE_API_TOKEN and DEMO_MODE=false.",
        )
    if not incident.dynatrace_problem_id:
        raise HTTPException(status_code=400, detail="This incident has no linked Dynatrace problem.")

    fix = ""
    if incident.impact and incident.impact.remediation_command:
        fix = f"\nRecommended fix: {incident.impact.remediation_command}"
    message = (
        f"[SpecterOps] Autonomous root-cause analysis ({incident.root_cause_confidence or '—'}% confidence)\n"
        f"{incident.root_cause_summary or 'See post-mortem.'}{fix}"
    )

    client = DynatraceClient()
    try:
        await client.add_problem_comment(incident.dynatrace_problem_id, message)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Dynatrace rejected the comment. The token needs 'problems.write' "
                "(classic) or the 'storage:events:write' permission (Grail/Gen3 tenants). "
                f"Details: {exc}"
            ),
        )
    return {"posted": True, "problem_id": incident.dynatrace_problem_id}


@router.delete("/{incident_id}")
async def delete_incident(incident_id: str):
    forget_incident(incident_id)
    return {"deleted": True, "incident_id": incident_id}
