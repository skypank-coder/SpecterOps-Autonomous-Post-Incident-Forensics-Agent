"""
BlameMapper — Agent 3 of 4.

Consumes the reconstructed timeline and builds a causal graph: nodes are
events/services, directed edges are "caused" relationships with confidence
weights. Identifies the single root-cause node and an overall confidence score.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict

from mcp import scenarios
from models.incident import (
    AgentStep,
    CausalEdge,
    CausalGraph,
    CausalNode,
    Incident,
)
from utils.gemini_client import gemini_json


def _parse_json_safe(raw: str, fallback: dict) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        cleaned = raw.strip()
        if "```" in cleaned:
            lines = cleaned.split("\n")
            cleaned = "\n".join(l for l in lines if not l.startswith("```"))
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return fallback


async def run_blame_mapper(incident: Incident) -> Incident:
    classification = incident.raw_data.get("classification", {})
    scenario = incident.raw_data.get("scenario") or scenarios.get_scenario("db_index")

    timeline_text = "\n".join(
        f"- [{e.timestamp.isoformat()}] ({e.severity.value}) {e.service}: {e.description}"
        for e in incident.timeline
    ) or "(no timeline events)"

    trace_summary = incident.raw_data.get("trace_summary", {})
    cascade = incident.raw_data.get("timeline_analysis", {}).get("cascade_chain", [])

    prompt = f"""You are a root-cause analysis engine. Build a causal graph for this incident.

CLASSIFICATION:
{json.dumps(classification, indent=2, default=str)}

TRACE SUMMARY:
{json.dumps(trace_summary, indent=2, default=str)}

OBSERVED CASCADE CHAIN: {' -> '.join(cascade) if cascade else 'unknown'}

RECONSTRUCTED TIMELINE:
{timeline_text}

Identify the single root cause and the causal chain to the user-facing impact.
Respond with JSON:
{{
  "root_cause_node_id": "node-1",
  "root_cause_explanation": "2-3 sentence technical explanation",
  "root_cause_category": "MISSING_DB_INDEX|MEMORY_LEAK|DEPLOYMENT|CONFIG_CHANGE|EXTERNAL_DEPENDENCY|TRAFFIC_SPIKE|OTHER",
  "confidence_pct": 92,
  "nodes": [
    {{"id": "node-1", "service": "postgresql", "event": "short event description", "timestamp_offset_seconds_ago": 1380, "is_root_cause": true}}
  ],
  "edges": [
    {{"source": "node-1", "target": "node-2", "relationship": "caused", "confidence": 0.95}}
  ]
}}

Provide at least 3 nodes forming a directed chain from root cause to impact."""

    offline = scenarios.offline_graph(scenario)
    try:
        raw = await gemini_json(prompt)
        result = _parse_json_safe(raw, offline)
        if not result.get("nodes") or len(result.get("nodes", [])) < 2:
            result = offline
    except Exception:
        result = offline

    now = datetime.utcnow()
    nodes = []
    for n in result.get("nodes", []):
        offset = int(n.get("timestamp_offset_seconds_ago", 0))
        nodes.append(
            CausalNode(
                id=n.get("id", "node"),
                service=n.get("service", "unknown"),
                event=n.get("event", ""),
                timestamp=now - timedelta(seconds=offset),
                is_root_cause=bool(n.get("is_root_cause", False)),
            )
        )

    edges = [
        CausalEdge(
            source=e.get("source", ""),
            target=e.get("target", ""),
            relationship=e.get("relationship", "caused"),
            confidence=float(e.get("confidence", 0.8)),
        )
        for e in result.get("edges", [])
    ]

    root_id = result.get("root_cause_node_id")
    if not any(n.is_root_cause for n in nodes) and nodes:
        nodes[0].is_root_cause = True
        root_id = root_id or nodes[0].id

    incident.causal_graph = CausalGraph(
        nodes=nodes, edges=edges, root_cause_node_id=root_id
    )
    incident.root_cause_summary = result.get("root_cause_explanation", "")
    incident.root_cause_confidence = int(result.get("confidence_pct", 0))
    incident.root_cause_category = result.get("root_cause_category", "OTHER")
    incident.raw_data["root_cause_category"] = incident.root_cause_category

    incident.agent_steps.append(
        AgentStep(
            agent_name="BlameMapper",
            action="Built causal graph and identified root cause",
            result=(
                f"Root cause: {result.get('root_cause_category')} | "
                f"confidence {incident.root_cause_confidence}% | "
                f"{len(nodes)} nodes, {len(edges)} edges"
            ),
        )
    )
    return incident
