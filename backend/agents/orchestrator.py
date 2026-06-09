"""
Orchestrator — drives the 4-agent SpecterOps pipeline and fans incident state
out to SSE subscribers in real time.

Pipeline:
  SentinelAgent (🛡️) -> TraceArchaeologist (🔍) -> BlameMapper (🎯) -> NarratorAgent (📝)

Every agent emits two broadcasts (start + complete), so a full run produces at
least 8 SSE events plus a final terminal event.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import storage
from agents.blame_agent import run_blame_mapper
from agents.narrator_agent import run_narrator
from agents.sentinel_agent import run_sentinel
from agents.trace_agent import run_trace_archaeologist
from models.incident import Incident, IncidentStatus

# In-memory hot cache; durably mirrored to Google Cloud Firestore (see storage.py).
INCIDENTS: Dict[str, Incident] = {}
SSE_QUEUES: Dict[str, List[asyncio.Queue]] = {}
# Per-incident event log so late subscribers can replay everything they missed.
# This makes the live stream robust to fast pipelines (e.g. offline fallback)
# where the analysis can complete before the dashboard finishes connecting.
SSE_HISTORY: Dict[str, List[str]] = {}


def _serialize(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, default=str)


async def _broadcast(incident_id: str, payload: Dict[str, Any]) -> None:
    """Record the event in history and push it to every live subscriber queue."""
    message = _serialize(payload)
    SSE_HISTORY.setdefault(incident_id, []).append(message)
    queues = SSE_QUEUES.get(incident_id, [])
    dead: List[asyncio.Queue] = []
    for q in queues:
        try:
            q.put_nowait(message)
        except Exception:
            dead.append(q)
    for q in dead:
        if q in queues:
            queues.remove(q)


def _incident_json(incident: Incident) -> Dict[str, Any]:
    return incident.model_dump(mode="json")


async def process_incident(incident_id: str, raw_alert: Dict[str, Any]) -> Incident:
    """Run the full forensics pipeline for one incident, broadcasting as it goes."""
    scenario = raw_alert.get("scenario") or {}
    incident = Incident(
        id=incident_id,
        title=raw_alert.get("title", "Production Incident"),
        owner=raw_alert.get("owner"),
        scenario_id=scenario.get("id"),
        dynatrace_problem_id=raw_alert.get("problemId"),
        status=IncidentStatus.DETECTING,
        analysis_started_at=datetime.utcnow(),
    )
    INCIDENTS[incident_id] = incident

    pipeline = [
        ("🛡️", "SentinelAgent", IncidentStatus.DETECTING, IncidentStatus.ANALYZING,
         "Classifying alert and extracting investigation targets",
         lambda inc: run_sentinel(inc, raw_alert)),
        ("🔍", "TraceArchaeologist", IncidentStatus.ANALYZING, IncidentStatus.ANALYZING,
         "Querying Dynatrace MCP: traces, logs, metrics, topology",
         run_trace_archaeologist),
        ("🎯", "BlameMapper", IncidentStatus.ANALYZING, IncidentStatus.ROOT_CAUSE_FOUND,
         "Building causal graph and isolating root cause",
         run_blame_mapper),
        ("📝", "NarratorAgent", IncidentStatus.WRITING_POSTMORTEM, IncidentStatus.WRITING_POSTMORTEM,
         "Writing the post-mortem with Gemini",
         run_narrator),
    ]

    try:
        for emoji, name, start_status, done_status, start_msg, runner in pipeline:
            incident.status = start_status
            await _broadcast(incident_id, {
                "status": start_status.value,
                "agent": name,
                "phase": "start",
                "message": f"{emoji} {name}: {start_msg}",
                "incident": _incident_json(incident),
            })

            incident = await runner(incident)
            incident.status = done_status
            INCIDENTS[incident_id] = incident

            last_step = incident.agent_steps[-1] if incident.agent_steps else None
            await _broadcast(incident_id, {
                "status": done_status.value,
                "agent": name,
                "phase": "complete",
                "message": f"{emoji} {name} complete",
                "step": last_step.model_dump(mode="json") if last_step else None,
                "incident": _incident_json(incident),
            })

        incident.status = IncidentStatus.COMPLETE
        incident.analysis_completed_at = datetime.utcnow()
        if incident.analysis_started_at:
            incident.analysis_duration_seconds = round(
                (incident.analysis_completed_at - incident.analysis_started_at).total_seconds(), 1
            )
        INCIDENTS[incident_id] = incident
        await _broadcast(incident_id, {
            "status": IncidentStatus.COMPLETE.value,
            "phase": "complete",
            "message": "✅ Forensics complete — post-mortem ready",
            "incident": _incident_json(incident),
        })
        await storage.save_incident(incident)
        return incident

    except Exception as exc:  # pragma: no cover - defensive
        incident.status = IncidentStatus.FAILED
        INCIDENTS[incident_id] = incident
        await _broadcast(incident_id, {
            "status": IncidentStatus.FAILED.value,
            "phase": "error",
            "message": f"❌ Pipeline failed: {exc}",
            "incident": _incident_json(incident),
        })
        await storage.save_incident(incident)
        return incident


def get_incident(incident_id: str) -> Optional[Incident]:
    return INCIDENTS.get(incident_id)


def get_all_incidents(owner: Optional[str] = None) -> List[Incident]:
    items = INCIDENTS.values()
    if owner:
        items = [i for i in items if i.owner == owner]
    return sorted(items, key=lambda i: i.detected_at, reverse=True)


async def hydrate_from_storage() -> int:
    """Load persisted incidents into memory on startup (no-op without a DB)."""
    docs = await storage.load_all()
    count = 0
    for doc in docs:
        try:
            inc = Incident.model_validate(doc)
            INCIDENTS.setdefault(inc.id, inc)
            count += 1
        except Exception:
            continue
    return count


def subscribe(incident_id: str) -> asyncio.Queue:
    """
    Register a subscriber queue and seed it with any events already emitted.

    This runs with no `await` boundaries, so registration + history replay are
    atomic with respect to `_broadcast`: an event is either already in history
    (replayed here) or arrives later via the queue — never both, never lost.
    """
    q: asyncio.Queue = asyncio.Queue()
    SSE_QUEUES.setdefault(incident_id, []).append(q)
    for message in SSE_HISTORY.get(incident_id, []):
        q.put_nowait(message)
    return q


def unsubscribe(incident_id: str, q: asyncio.Queue) -> None:
    queues = SSE_QUEUES.get(incident_id, [])
    if q in queues:
        queues.remove(q)
    if not queues and incident_id in SSE_QUEUES:
        SSE_QUEUES.pop(incident_id, None)


def forget_incident(incident_id: str) -> None:
    """Drop all state for an incident (used by the delete endpoint)."""
    INCIDENTS.pop(incident_id, None)
    SSE_QUEUES.pop(incident_id, None)
    SSE_HISTORY.pop(incident_id, None)
    if storage.enabled():
        try:
            asyncio.get_running_loop().create_task(storage.delete_incident(incident_id))
        except RuntimeError:
            pass  # no running loop (e.g. sync context) — DB row will age out
