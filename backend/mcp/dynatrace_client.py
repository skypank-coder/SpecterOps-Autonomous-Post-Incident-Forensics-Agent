"""
Dynatrace MCP client.

Acts as the SpecterOps connector to Dynatrace observability data: problems,
distributed traces, logs, metrics and service topology. When DEMO_MODE is true
(the default) every call returns deterministic, scenario-driven simulation data
after a short delay so the system runs end-to-end with zero external accounts.
When DEMO_MODE is false it talks to the live Dynatrace REST API.
"""
from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, Optional

import httpx

from mcp import scenarios


def _demo_mode() -> bool:
    return os.getenv("DEMO_MODE", "true").lower() in ("1", "true", "yes")


_DT_PLACEHOLDERS = {
    "",
    "https://your-env-id.live.dynatrace.com",
    "your_dynatrace_api_token_here",
}


def dynatrace_configured() -> bool:
    url = os.getenv("DYNATRACE_URL", "").strip()
    token = os.getenv("DYNATRACE_API_TOKEN", "").strip()
    return url not in _DT_PLACEHOLDERS and token not in _DT_PLACEHOLDERS


class DynatraceClient:
    """Async client for the Dynatrace v2 API with a scenario-driven simulation fallback."""

    def __init__(self, problem_id: Optional[str] = None, scenario: Optional[Dict[str, Any]] = None):
        self.problem_id = problem_id or "P-DEMO-001"
        self.scenario = scenario or scenarios.get_scenario("db_index")
        self.base_url = os.getenv("DYNATRACE_URL", "").rstrip("/")
        self.token = os.getenv("DYNATRACE_API_TOKEN", "")
        self.demo = _demo_mode()

    # ------------------------------------------------------------------ #
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Api-Token {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{self.base_url}{path}", headers=self._headers(), params=params)
            resp.raise_for_status()
            return resp.json()

    async def _try_get(self, path: str, params: Optional[Dict[str, Any]] = None,
                       fallback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Resilient GET: a single unavailable endpoint must not abort the pipeline."""
        try:
            return await self._get(path, params)
        except Exception:
            return fallback if fallback is not None else {}

    # ------------------------------------------------------------------ #
    async def get_open_problems(self, window_minutes: int = 120) -> Dict[str, Any]:
        """List recent OPEN problems (used to auto-pull a real incident)."""
        if self.demo:
            await asyncio.sleep(0.3)
            return {"totalCount": 1, "problems": [await self.get_problem_details()]}
        params = {
            "from": f"now-{window_minutes}m",
            "to": "now",
            "problemSelector": 'status("OPEN")',
            "pageSize": "25",
        }
        return await self._get("/api/v2/problems", params=params)

    async def get_problem_by_id(self, problem_id: str) -> Dict[str, Any]:
        """Full problem object incl. evidence (live), or mock in demo mode."""
        if self.demo:
            await asyncio.sleep(0.2)
            return await self.get_problem_details()
        return await self._try_get(f"/api/v2/problems/{problem_id}", fallback={})

    async def add_problem_comment(self, problem_id: str, message: str) -> None:
        """Post a comment back onto a Dynatrace problem (requires problems.write)."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{self.base_url}/api/v2/problems/{problem_id}/comments",
                headers=self._headers(),
                json={"message": message, "context": "SpecterOps"},
            )
            resp.raise_for_status()

    async def get_problem_details(self) -> Dict[str, Any]:
        if self.demo:
            await asyncio.sleep(0.3)
            return {
                "problemId": self.problem_id,
                "title": self.scenario["title"],
                "severityLevel": "PERFORMANCE",
                "status": "OPEN",
                "affectedEntities": [
                    {"entityId": {"id": f"SERVICE-{i}", "type": "SERVICE"}, "name": s}
                    for i, s in enumerate(self.scenario["services"])
                ],
            }
        return await self._get(f"/api/v2/problems/{self.problem_id}")

    async def get_traces(self, service_name: str, window_minutes: int = 30) -> Dict[str, Any]:
        if self.demo:
            await asyncio.sleep(0.3)
            return scenarios.gen_traces(self.scenario)
        # NOTE: Dynatrace does not expose a stable public "read traces" REST
        # endpoint (distributed traces live in Grail/DQL, which is tenant- and
        # license-dependent). For the live path we rely on problems + metrics +
        # logs + topology, which are universally available, and degrade traces
        # gracefully so the investigation still completes.
        return {"service": service_name, "totalCount": 0, "errorCount": 0, "traces": []}

    async def get_logs(self, service_name: str, window_minutes: int = 30) -> Dict[str, Any]:
        if self.demo:
            await asyncio.sleep(0.3)
            return scenarios.gen_logs(self.scenario)
        # Classic Log Monitoring v2 is a GET with query params (Grail tenants may
        # differ). Best-effort: return empty results if logs aren't available.
        params = {
            "query": f'dt.entity.service.name="{service_name}"',
            "from": f"now-{window_minutes}m",
            "to": "now",
            "limit": "100",
            "sort": "timestamp",
        }
        data = await self._try_get("/api/v2/logs/search", params=params,
                                   fallback={"results": []})
        if "results" not in data:
            data["results"] = data.get("logs", [])
        return data

    async def get_metrics(self, metric_key: str, service_name: str,
                          entity_ids: Optional[list] = None) -> Dict[str, Any]:
        if self.demo:
            await asyncio.sleep(0.3)
            return scenarios.gen_metrics(self.scenario, metric_key)
        # Prefer the real affected entity IDs from the problem; fall back to name.
        if entity_ids:
            ids = ",".join(f'"{i}"' for i in entity_ids)
            entity_selector = f"entityId({ids})"
        else:
            entity_selector = f'type(SERVICE),entityName("{service_name}")'
        params = {
            "metricSelector": metric_key,
            "entitySelector": entity_selector,
            "from": "now-30m",
            "to": "now",
            "resolution": "1m",
        }
        return await self._try_get("/api/v2/metrics/query", params=params,
                                   fallback={"result": []})

    async def get_topology(self, service_name: str) -> Dict[str, Any]:
        if self.demo:
            await asyncio.sleep(0.3)
            return scenarios.gen_topology(self.scenario)
        params = {
            "entitySelector": f'type(SERVICE),entityName("{service_name}")',
            "fields": "+fromRelationships,+toRelationships",
            "from": "now-30m",
            "to": "now",
        }
        return await self._try_get("/api/v2/entities", params=params,
                                   fallback={"entities": []})
