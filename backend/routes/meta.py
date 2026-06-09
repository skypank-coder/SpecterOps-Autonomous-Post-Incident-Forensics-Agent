"""Metadata endpoints: runtime configuration status and the scenario library."""
from __future__ import annotations

import os

from fastapi import APIRouter

import storage
from mcp import scenarios
from mcp.dynatrace_client import DynatraceClient, dynatrace_configured
from utils.gemini_client import active_model, gemini_available

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
        },
        "dynatrace": {
            "connected": dynatrace_configured() and not demo_mode,
            "configured": dynatrace_configured(),
        },
        "storage": {
            "connected": storage.enabled(),
            "backend": "mongodb" if storage.enabled() else "in-memory",
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
    if _demo_mode() or not dynatrace_configured():
        return {"connected": False, "problems": []}

    client = DynatraceClient()
    try:
        data = await client.get_open_problems()
    except Exception as exc:  # surface, don't crash
        return {"connected": True, "error": str(exc)[:200], "problems": []}

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
