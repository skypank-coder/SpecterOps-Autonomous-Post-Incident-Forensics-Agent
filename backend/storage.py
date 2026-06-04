"""
Optional persistence layer.

If MONGODB_URI is configured (and `motor` is installed) incidents are persisted
to MongoDB so history survives restarts. Otherwise every function is a no-op and
the app falls back to in-memory storage — so it always runs with zero setup.

Heavy raw telemetry (`raw_data`) is stripped before persisting to keep documents
lean; the dashboard only needs the derived fields.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List

from dotenv import load_dotenv

# Load .env here too — storage is imported early (before other modules that call
# load_dotenv), so without this the MONGODB_URI could read as empty at import.
load_dotenv()

_PLACEHOLDERS = {"", "mongodb+srv://user:pass@cluster.mongodb.net/specterops"}
_URI = os.getenv("MONGODB_URI", "").strip()

_client = None
_col = None

if _URI and _URI not in _PLACEHOLDERS:
    try:
        import motor.motor_asyncio as _motor

        _client = _motor.AsyncIOMotorClient(_URI, serverSelectionTimeoutMS=3000)
        _col = _client["specterops"]["incidents"]
    except Exception:  # motor missing or bad URI — degrade to in-memory
        _client = None
        _col = None


def enabled() -> bool:
    return _col is not None


def _slim(incident) -> Dict[str, Any]:
    doc = incident.model_dump(mode="json")
    doc.pop("raw_data", None)
    doc["_id"] = doc["id"]
    return doc


async def save_incident(incident) -> None:
    if _col is None:
        return
    try:
        doc = _slim(incident)
        await _col.replace_one({"_id": doc["_id"]}, doc, upsert=True)
    except Exception:
        pass


async def delete_incident(incident_id: str) -> None:
    if _col is None:
        return
    try:
        await _col.delete_one({"_id": incident_id})
    except Exception:
        pass


async def load_all() -> List[Dict[str, Any]]:
    if _col is None:
        return []
    try:
        out: List[Dict[str, Any]] = []
        async for doc in _col.find().sort("detected_at", -1).limit(200):
            doc.pop("_id", None)
            out.append(doc)
        return out
    except Exception:
        return []
