"""
Backward-compatible thin wrappers around the scenario engine.

The flagship "missing database index" scenario is the default, so existing
imports (and tests) that call these helpers keep working unchanged. New code
should prefer `mcp.scenarios` directly.
"""
from __future__ import annotations

from typing import Any, Dict

from connectors import scenarios


def _db_index() -> Dict[str, Any]:
    return scenarios.get_scenario("db_index")


def mock_problem_details() -> Dict[str, Any]:
    s = _db_index()
    return {
        "problemId": "P-DEMO-001",
        "title": s["title"],
        "severityLevel": "PERFORMANCE",
        "status": "OPEN",
        "affectedEntities": [
            {"entityId": {"id": f"SERVICE-{i}", "type": "SERVICE"}, "name": svc}
            for i, svc in enumerate(s["services"])
        ],
    }


def mock_traces(service_name: str) -> Dict[str, Any]:
    return scenarios.gen_traces(_db_index())


def mock_logs(service_name: str) -> Dict[str, Any]:
    return scenarios.gen_logs(_db_index())


def mock_metrics(metric_key: str, service_name: str) -> Dict[str, Any]:
    return scenarios.gen_metrics(_db_index(), metric_key)


def mock_topology(service_name: str) -> Dict[str, Any]:
    return scenarios.gen_topology(_db_index())
