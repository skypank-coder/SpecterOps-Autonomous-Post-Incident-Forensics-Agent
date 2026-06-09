"""
Persistence layer — Google Cloud Firestore.

Uses Firestore (a Google Cloud database) so the whole stack stays on Google
Cloud. On Cloud Run, auth is the service's own identity (Application Default
Credentials) — no connection string, no IP allowlist. If Firestore isn't
available (e.g. local dev without ADC), every function degrades to a no-op and
the app falls back to in-memory storage, so it always runs.

Heavy raw telemetry (`raw_data`) is stripped before persisting to keep documents
lean; the dashboard only needs the derived fields.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv()

_PLACEHOLDERS = {"", "your_gcp_project_id"}
_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "").strip()
_DISABLED = os.getenv("FIRESTORE_DISABLED", "").lower() in ("1", "true", "yes")
_COLLECTION = "incidents"

_fs = None
_client = None
if not _DISABLED and _PROJECT and _PROJECT not in _PLACEHOLDERS:
    try:
        from google.cloud import firestore as _fs

        _client = _fs.AsyncClient(project=_PROJECT)
    except Exception:  # library missing or no credentials
        _client = None
        _fs = None


def enabled() -> bool:
    return _client is not None


def backend_name() -> str:
    return "firestore" if enabled() else "in-memory"


def _slim(incident) -> Dict[str, Any]:
    doc = incident.model_dump(mode="json")
    doc.pop("raw_data", None)
    return doc


async def save_incident(incident) -> None:
    if _client is None:
        return
    try:
        doc = _slim(incident)
        await _client.collection(_COLLECTION).document(doc["id"]).set(doc)
    except Exception:
        pass


async def delete_incident(incident_id: str) -> None:
    if _client is None:
        return
    try:
        await _client.collection(_COLLECTION).document(incident_id).delete()
    except Exception:
        pass


async def load_all() -> List[Dict[str, Any]]:
    if _client is None:
        return []
    try:
        out: List[Dict[str, Any]] = []
        query = (
            _client.collection(_COLLECTION)
            .order_by("detected_at", direction=_fs.Query.DESCENDING)
            .limit(200)
        )
        async for snap in query.stream():
            out.append(snap.to_dict())
        return out
    except Exception:
        return []
