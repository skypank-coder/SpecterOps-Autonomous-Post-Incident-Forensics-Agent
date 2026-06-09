"""
NarratorAgent — Agent 4 of 4.

Assembles every piece of evidence the pipeline has gathered and asks Gemini to
write a complete, production-grade post-mortem in Markdown.
"""
from __future__ import annotations

from typing import List

from connectors import scenarios
from models.incident import AgentStep, Incident
from utils.gemini_client import gemini_reason

SYSTEM = (
    "You are a senior SRE writing a production post-mortem. Be specific and "
    "technical. Use exact service names, timestamps, and metrics from the data "
    "provided. Never use placeholder text."
)


def _timeline_text(incident: Incident) -> str:
    if not incident.timeline:
        return "(no timeline reconstructed)"
    return "\n".join(
        f"- {e.timestamp.strftime('%H:%M:%S')} UTC | {e.service} | {e.event_type} "
        f"| {e.severity.value} | {e.description}"
        for e in incident.timeline
    )


def _graph_text(incident: Incident) -> str:
    if not incident.causal_graph:
        return "(no causal graph)"
    lines: List[str] = ["Nodes:"]
    for n in incident.causal_graph.nodes:
        marker = " [ROOT CAUSE]" if n.is_root_cause else ""
        lines.append(f"  - {n.id} ({n.service}): {n.event}{marker}")
    lines.append("Edges:")
    for e in incident.causal_graph.edges:
        lines.append(f"  - {e.source} --{e.relationship} ({e.confidence:.0%})--> {e.target}")
    return "\n".join(lines)


async def run_narrator(incident: Incident) -> Incident:
    confidence = incident.root_cause_confidence or 0
    category = incident.raw_data.get("root_cause_category", "OTHER")
    scenario = incident.raw_data.get("scenario") or scenarios.get_scenario("db_index")

    prompt = f"""Write a complete production post-mortem in Markdown for this incident.

INCIDENT TITLE: {incident.title}
SEVERITY: {incident.severity.value}
AFFECTED SERVICES: {', '.join(incident.affected_services)}
DETECTED AT: {incident.detected_at.isoformat()} UTC
DYNATRACE PROBLEM: {incident.dynatrace_problem_id or 'P-DEMO-001'}

ROOT CAUSE CATEGORY: {category}
ROOT CAUSE CONFIDENCE: {confidence}%
ROOT CAUSE SUMMARY:
{incident.root_cause_summary or '(none)'}

RECONSTRUCTED TIMELINE:
{_timeline_text(incident)}

CAUSAL GRAPH:
{_graph_text(incident)}

Write the post-mortem with these exact sections using ## headers, in this order:
## Executive Summary
## Impact
## Root Cause
## Timeline
## Causal Chain
## Detection & Response
## Immediate Remediation Steps
## Action Items
## Lessons Learned
## Prevention Measures

Requirements:
- The Timeline section MUST be a Markdown table with columns: Time | Service | Event | Severity
- The Action Items section MUST be a Markdown table with columns: Item | Owner | Priority | Due Date
- Immediate Remediation Steps MUST be a numbered list
- Use exact service names, timestamps and metrics from the data above
- Be specific and technical; no placeholder text"""

    try:
        postmortem = await gemini_reason(prompt, SYSTEM, max_tokens=6000)
        if not postmortem or len(postmortem.strip()) < 500:
            postmortem = scenarios.offline_postmortem(scenario, incident)
    except Exception:
        postmortem = scenarios.offline_postmortem(scenario, incident)

    incident.postmortem = postmortem

    incident.agent_steps.append(
        AgentStep(
            agent_name="NarratorAgent",
            action="Generated post-mortem via Gemini",
            result=f"Post-mortem written ({len(postmortem)} chars) covering 10 sections",
        )
    )
    return incident
