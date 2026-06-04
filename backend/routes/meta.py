"""Metadata endpoints: runtime configuration status and the scenario library."""
from __future__ import annotations

import os

from fastapi import APIRouter

import storage
from mcp import scenarios
from mcp.dynatrace_client import dynatrace_configured
from utils.gemini_client import active_model, gemini_available

router = APIRouter(prefix="/api", tags=["meta"])


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
