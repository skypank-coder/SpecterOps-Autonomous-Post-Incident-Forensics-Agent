"""Dynatrace webhook endpoint — kicks off the pipeline from a real alert."""
from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict

from fastapi import APIRouter

from agents.orchestrator import process_incident

router = APIRouter(prefix="/api/webhook", tags=["webhook"])


@router.post("/dynatrace")
async def dynatrace_webhook(payload: Dict[str, Any]):
    incident_id = str(uuid.uuid4())
    asyncio.create_task(process_incident(incident_id, payload))
    return {"incident_id": incident_id, "status": "analysis_started"}
