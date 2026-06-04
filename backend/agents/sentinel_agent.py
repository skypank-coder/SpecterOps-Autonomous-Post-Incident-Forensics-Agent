"""
SentinelAgent — Agent 1 of 4.

Classifies an incoming Dynatrace alert and extracts the investigation targets
(primary service, severity, category, metrics to pull) that the rest of the
pipeline depends on.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from mcp import scenarios
from models.incident import AgentStep, Incident, IncidentSeverity
from utils.gemini_client import gemini_json

FALLBACK_METRICS = ["builtin:service.response.time", "builtin:service.errors.total.rate"]


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


async def run_sentinel(incident: Incident, raw_alert: Dict[str, Any]) -> Incident:
    alert_str = json.dumps(raw_alert, indent=2, default=str)

    prompt = f"""Analyze this Dynatrace production alert and classify it.

ALERT DATA:
{alert_str}

Extract the following information and respond with JSON:
{{
  "primary_service": "the most directly affected service name",
  "title": "concise technical incident title under 80 characters",
  "severity": "one of: CRITICAL HIGH MEDIUM LOW",
  "affected_services": ["list", "of", "service", "names"],
  "category": "one of: DATABASE_ISSUE MEMORY_LEAK NETWORK DEPLOYMENT DEPENDENCY_FAILURE TRAFFIC_SPIKE UNKNOWN",
  "metrics_to_investigate": ["builtin:service.response.time", "builtin:service.errors.total.rate"],
  "classification_reasoning": "one sentence explanation of your classification"
}}"""

    affected = [e.get("name", "") for e in raw_alert.get("affectedEntities", [])]
    affected = [a for a in affected if a]

    # The scenario rides in the alert payload (built-in preset or a custom
    # incident). It drives the simulated telemetry and the offline analysis.
    scenario = raw_alert.get("scenario") or scenarios.get_scenario("db_index")
    incident.raw_data["scenario"] = scenario

    fallback = {
        "primary_service": affected[0] if affected else "unknown-service",
        "title": raw_alert.get("title", "Production Incident"),
        "severity": "HIGH",
        "affected_services": affected,
        "category": "UNKNOWN",
        "metrics_to_investigate": FALLBACK_METRICS,
        "classification_reasoning": "Default classification — Gemini response was not valid JSON",
    }

    # When Gemini is unavailable, fall back to the scenario's classification.
    offline = scenarios.offline_classification(scenario)

    try:
        raw = await gemini_json(prompt)
        result = _parse_json_safe(raw, fallback)
    except Exception:
        result = offline

    incident.title = result.get("title", incident.title)
    try:
        incident.severity = IncidentSeverity(result.get("severity", "HIGH"))
    except ValueError:
        incident.severity = IncidentSeverity.HIGH
    incident.affected_services = result.get("affected_services", affected)
    incident.raw_data["classification"] = result

    incident.agent_steps.append(
        AgentStep(
            agent_name="SentinelAgent",
            action="Alert classification via Gemini",
            result=(
                f"Category: {result.get('category')} | "
                f"Primary: {result.get('primary_service')} | "
                f"Severity: {result.get('severity')} | "
                f"{result.get('classification_reasoning', '')}"
            ),
        )
    )
    return incident
