"""Metadata endpoints: runtime configuration status and the scenario library."""
from __future__ import annotations

import os

from fastapi import APIRouter

import storage
from connectors import dynatrace_mcp, scenarios
from connectors.dynatrace_client import DynatraceClient, dynatrace_configured
from utils.gemini_client import active_model, gemini_available, provider as gemini_provider

router = APIRouter(prefix="/api", tags=["meta"])


def _demo_mode() -> bool:
    return os.getenv("DEMO_MODE", "true").lower() in ("1", "true", "yes")


@router.get("/config")
async def get_config():
    """What's actually wired up — used by the dashboard's connection badges."""
    demo_mode = os.getenv("DEMO_MODE", "true").lower() in ("1", "true", "yes")
    return {
        "demo_mode": demo_mode,
        "gemini": {
            "connected": gemini_available(),
            "model": active_model() if gemini_available() else None,
            "provider": gemini_provider(),  # "vertex" | "aistudio" | "none"
        },
        "dynatrace": {
            "connected": (dynatrace_mcp.mcp_configured() or dynatrace_configured()) and not demo_mode,
            "configured": dynatrace_mcp.mcp_configured() or dynatrace_configured(),
            "via": "mcp" if dynatrace_mcp.mcp_configured() else ("rest" if dynatrace_configured() else None),
        },
        "storage": {
            "connected": storage.enabled(),
            "backend": storage.backend_name(),
        },
        "slack": {"connected": _slack_configured()},
    }


def _slack_configured() -> bool:
    url = os.getenv("SLACK_WEBHOOK_URL", "").strip()
    return bool(url) and not url.startswith("https://hooks.slack.com/services/your")


@router.get("/scenarios")
async def get_scenarios():
    return scenarios.list_scenarios()


@router.get("/dynatrace/problems")
async def list_dynatrace_problems():
    """List open problems from the live Dynatrace tenant so the user can pick one."""
    if _demo_mode():
        return {"connected": False, "problems": []}

    # Preferred path: the official Dynatrace MCP server.
    if dynatrace_mcp.mcp_configured():
        try:
            probs = await dynatrace_mcp.list_problems(status="ACTIVE", timeframe="2h", limit=25)
        except Exception as exc:
            return {"connected": True, "via": "mcp", "error": str(exc)[:200], "problems": []}
        out = [{
            "id": p["id"],
            "display_id": p["display_id"],
            "title": p["title"],
            "severity": p["severity"],
            "status": p["status"],
            "category": p["category"],
            "services": [],
            "service_count": 0,
            "start_time": None,
        } for p in probs]
        return {"connected": True, "via": "mcp", "problems": out}

    if not dynatrace_configured():
        return {"connected": False, "problems": []}

    client = DynatraceClient()
    try:
        data = await client.get_open_problems()
    except Exception as exc:  # surface, don't crash
        return {"connected": True, "via": "rest", "error": str(exc)[:200], "problems": []}

    out = []
    for p in (data.get("problems", []) or [])[:25]:
        services = [e.get("name", "") for e in p.get("affectedEntities", []) if e.get("name")]
        out.append({
            "id": p.get("problemId") or p.get("displayId"),
            "title": p.get("title", "Problem"),
            "severity": scenarios._DT_SEVERITY.get(p.get("severityLevel", ""), "HIGH"),
            "severity_level": p.get("severityLevel"),
            "status": p.get("status"),
            "services": services[:4],
            "service_count": len(services),
            "start_time": p.get("startTime"),
        })
    return {"connected": True, "problems": out}
