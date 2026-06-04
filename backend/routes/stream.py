"""Server-Sent Events endpoint — streams live incident state to the dashboard."""
from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from agents.orchestrator import get_incident, subscribe, unsubscribe

router = APIRouter(prefix="/api/stream", tags=["stream"])


@router.get("/{incident_id}")
async def stream_incident(incident_id: str):
    async def generator():
        # Send current state immediately on connect. This is a neutral "hello"
        # (type=connected, no terminal status) so clients don't stop early when
        # they attach to an already-finished incident — the full event history
        # is replayed right after via the subscriber queue.
        current = get_incident(incident_id)
        if current:
            yield {"data": json.dumps({
                "type": "connected",
                "message": "Connected to SpecterOps stream",
                "incident": current.model_dump(mode="json"),
            }, default=str)}

        q = subscribe(incident_id)
        try:
            while True:
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=25.0)
                    yield {"data": msg}
                    parsed = json.loads(msg)
                    if parsed.get("status") in ("COMPLETE", "FAILED"):
                        break
                except asyncio.TimeoutError:
                    yield {"data": json.dumps({"type": "heartbeat"})}
        finally:
            unsubscribe(incident_id, q)

    return EventSourceResponse(generator())
