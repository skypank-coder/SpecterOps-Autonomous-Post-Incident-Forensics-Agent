"""
SpecterOps domain models.

Pydantic models describing an incident as it flows through the 4-agent pipeline:
SentinelAgent -> TraceArchaeologist -> BlameMapper -> NarratorAgent.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class IncidentSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class IncidentStatus(str, Enum):
    DETECTING = "DETECTING"
    ANALYZING = "ANALYZING"
    ROOT_CAUSE_FOUND = "ROOT_CAUSE_FOUND"
    WRITING_POSTMORTEM = "WRITING_POSTMORTEM"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class AgentStep(BaseModel):
    agent_name: str
    action: str
    result: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TimelineEvent(BaseModel):
    timestamp: datetime
    service: str
    event_type: str
    description: str
    severity: IncidentSeverity
    is_root_cause_candidate: bool = False


class CausalNode(BaseModel):
    id: str
    service: str
    event: str
    timestamp: datetime
    is_root_cause: bool = False


class CausalEdge(BaseModel):
    source: str
    target: str
    relationship: str
    confidence: float


class CausalGraph(BaseModel):
    nodes: List[CausalNode] = Field(default_factory=list)
    edges: List[CausalEdge] = Field(default_factory=list)
    root_cause_node_id: Optional[str] = None


class IncidentImpact(BaseModel):
    """Headline impact numbers surfaced prominently on the dashboard."""
    error_rate_pct: Optional[float] = None
    p99_latency_ms: Optional[float] = None
    baseline_latency_ms: Optional[float] = None
    latency_spike_ratio: Optional[float] = None
    affected_traces: Optional[int] = None
    error_traces: Optional[int] = None
    remediation_command: Optional[str] = None


class Incident(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "Production Incident"
    owner: Optional[str] = None  # user id/email when created by a signed-in user
    scenario_id: Optional[str] = None
    severity: IncidentSeverity = IncidentSeverity.HIGH
    affected_services: List[str] = Field(default_factory=list)
    start_time: datetime = Field(default_factory=datetime.utcnow)
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    status: IncidentStatus = IncidentStatus.DETECTING
    agent_steps: List[AgentStep] = Field(default_factory=list)
    timeline: List[TimelineEvent] = Field(default_factory=list)
    causal_graph: Optional[CausalGraph] = None
    root_cause_summary: Optional[str] = None
    root_cause_confidence: Optional[int] = None
    root_cause_category: Optional[str] = None
    impact: Optional[IncidentImpact] = None
    postmortem: Optional[str] = None
    dynatrace_problem_id: Optional[str] = None
    # Timing — used to prove the "diagnosed in under 60 seconds" claim on screen.
    analysis_started_at: Optional[datetime] = None
    analysis_completed_at: Optional[datetime] = None
    analysis_duration_seconds: Optional[float] = None
    raw_data: Dict[str, Any] = Field(default_factory=dict)
