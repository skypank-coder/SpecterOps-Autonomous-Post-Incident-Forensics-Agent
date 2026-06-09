"""
Dynatrace MCP integration.

SpecterOps connects to the **official Dynatrace MCP server**
(`@dynatrace-oss/dynatrace-mcp-server`) as an MCP **client** over the Model
Context Protocol — fulfilling the hackathon requirement to "integrate a Partner
Entity's MCP server."

The TraceArchaeologist agent calls real MCP tools to pull live data from the
Dynatrace tenant:
  * `list_problems`       — open problems (Davis)
  * `execute_dql`         — logs / spans / metrics / events via Grail DQL
  * `find_entity_by_name` — resolve monitored entities

A single MCP server process + session is spawned lazily and reused, so the
OAuth browser login happens only ONCE per backend process. For fully headless /
hosted use, set OAUTH_CLIENT_ID / OAUTH_CLIENT_SECRET / OAUTH_URN (or a
DT_PLATFORM_TOKEN). When MCP is unavailable, callers fall back to the simulation
path so the product never breaks.
"""
from __future__ import annotations

import asyncio
import os
import re
from contextlib import AsyncExitStack
from datetime import timedelta
from typing import Any, Dict, List

_NPX = "npx.cmd" if os.name == "nt" else "npx"

_DT_SEVERITY = {
    "AVAILABILITY": "CRITICAL",
    "ERROR": "CRITICAL",
    "PERFORMANCE": "HIGH",
    "RESOURCE_CONTENTION": "HIGH",
    "SLOWDOWN": "HIGH",
    "CUSTOM_ALERT": "MEDIUM",
    "MONITORING_UNAVAILABLE": "MEDIUM",
}

# Persistent server + session (spawned once, reused).
_stack: AsyncExitStack | None = None
_session = None
_init_lock = asyncio.Lock()
_call_lock = asyncio.Lock()


def dt_environment() -> str:
    return os.getenv("DT_ENVIRONMENT", "").strip()


def mcp_configured() -> bool:
    """True when a Dynatrace platform environment is configured for MCP."""
    return bool(dt_environment())


def _server_env() -> Dict[str, str]:
    return {**os.environ, "DT_ENVIRONMENT": dt_environment(), "DT_MCP_DISABLE_TELEMETRY": "true"}


async def _get_session():
    """Lazily spawn the Dynatrace MCP server once and keep the session alive."""
    global _stack, _session
    if _session is not None:
        return _session
    async with _init_lock:
        if _session is not None:
            return _session
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        stack = AsyncExitStack()
        params = StdioServerParameters(
            command=_NPX,
            args=["-y", "@dynatrace-oss/dynatrace-mcp-server"],
            env=_server_env(),
        )
        read, write = await stack.enter_async_context(stdio_client(params))
        session = await stack.enter_async_context(
            ClientSession(read, write, read_timeout_seconds=timedelta(seconds=120))
        )
        await session.initialize()
        _stack = stack
        _session = session
        return _session


async def close() -> None:
    """Tear down the MCP session (called on shutdown / after an auth failure)."""
    global _stack, _session
    if _stack is not None:
        try:
            await _stack.aclose()
        except Exception:
            pass
    _stack = None
    _session = None


def _text(result) -> str:
    return "\n".join(getattr(c, "text", "") for c in result.content)


async def _call(tool: str, args: Dict[str, Any]) -> str:
    """Call an MCP tool on the shared session; reset + retry once on failure."""
    for attempt in (1, 2):
        try:
            session = await _get_session()
            async with _call_lock:
                result = await session.call_tool(tool, args)
            return _text(result)
        except Exception:
            await close()
            if attempt == 2:
                raise
    return ""


def parse_problems(text: str) -> List[Dict[str, Any]]:
    """Parse the human-readable `list_problems` output into structured records."""
    out: List[Dict[str, Any]] = []
    for chunk in re.split(r"(?=Problem P-\d+)", text):
        m_disp = re.search(r"Problem (P-\d+)", chunk)
        if not m_disp:
            continue
        m_id = re.search(r"event\.id`?\s*([\-\w]+)\)\)", chunk)
        m_status = re.search(r"event\.status (\w+)", chunk)
        m_cat = re.search(r"event\.category (\w+):\s*(.+?)\s*-", chunk)
        m_dur = re.search(r"duration of (\d+)s", chunk)
        m_users = re.search(r"affects (\d+) users", chunk)
        category = m_cat.group(1) if m_cat else ""
        out.append({
            "display_id": m_disp.group(1),
            "id": m_id.group(1) if m_id else m_disp.group(1),
            "status": m_status.group(1) if m_status else "",
            "category": category,
            "severity": _DT_SEVERITY.get(category, "HIGH"),
            "title": m_cat.group(2).strip() if m_cat else "Dynatrace problem",
            "duration_s": int(m_dur.group(1)) if m_dur else None,
            "affected_users": int(m_users.group(1)) if m_users else None,
        })
    return out


async def list_problems(status: str = "ACTIVE", timeframe: str = "2h", limit: int = 25) -> List[Dict[str, Any]]:
    """Live problems via the MCP `list_problems` tool."""
    text = await _call(
        "list_problems",
        {"status": status, "timeframe": timeframe, "maxProblemsToDisplay": limit},
    )
    return parse_problems(text)


async def gather_evidence(service_hint: str = "", problem_id: str = "", limit: int = 25) -> Dict[str, Any]:
    """Pull real investigation evidence via DQL on the shared MCP session."""
    evidence: Dict[str, Any] = {"logs": "", "events": "", "entity": "", "tool_calls": []}

    async def _try(tool: str, args: Dict[str, Any]) -> str:
        try:
            txt = await _call(tool, args)
            evidence["tool_calls"].append(tool)
            return txt
        except Exception:
            return ""

    evidence["logs"] = (await _try("execute_dql", {
        "dqlStatement": (
            "fetch logs, from:now()-2h "
            '| filter loglevel == "ERROR" or loglevel == "WARN" '
            "| sort timestamp desc | limit " + str(limit)
        )
    }))[:4000]

    evidence["events"] = (await _try("execute_dql", {
        "dqlStatement": "fetch events, from:now()-2h | sort timestamp desc | limit 10"
    }))[:2500]

    if service_hint:
        evidence["entity"] = (await _try("find_entity_by_name", {"entityNames": [service_hint]}))[:1500]

    return evidence


async def environment_info() -> str:
    return await _call("get_environment_info", {})
