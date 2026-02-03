from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


# ============================================================================
# Canonical Models (minimal + future-proof)
# ============================================================================


LeadStatus = Literal[
    "new",
    "contacted",
    "qualified",
    "proposal",
    "negotiation",
    "won",
    "lost",
]


CampaignStatus = Literal["active", "paused", "completed", "draft"]


AgentType = Literal["caller", "emailer", "qualifier", "scheduler"]
AgentStatus = Literal["active", "inactive", "error"]


CallAttemptStatus = Literal[
    "queued",
    "initiated",
    "ringing",
    "in_progress",
    "completed",
    "failed",
    "no_answer",
    "busy",
    "canceled",
]


EventType = Literal[
    "leadgen.run.started",
    "leadgen.run.completed",
    "leadgen.run.failed",
    "segment.created",
    "campaign.created",
    "campaign.status.updated",
    "campaign.executed",
    "lead.updated",
    "call.attempt.created",
    "call.attempt.updated",
    "call.result.created",
    "voice_agent.tool_log",
    "error",
]


class Lead(BaseModel):
    # Internal ID for cross-system joins.
    lead_id: str

    # External identifiers (optional but important for dedupe + traceability).
    place_id: Optional[str] = None

    name: str
    company: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None

    status: LeadStatus = "new"
    score: float = 0.0

    campaign_id: Optional[str] = None
    assigned_agent_id: Optional[str] = None

    notes: list[str] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)

    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

    metadata: dict[str, Any] = Field(default_factory=dict)


class LeadGenFilter(BaseModel):
    # This is the UI-driven filter schema. Some fields may not be used by the
    # current lead engine, but we store them for forward compatibility.
    query: str
    location: str
    radius_miles: int = 25
    max_results: int = 100
    max_pages: int = 3  # Lead engine supports 1-3

    no_crawl: bool = False
    include_emails: bool = True
    include_phones: bool = True


LeadGenRunStatus = Literal["pending", "running", "completed", "failed"]


class LeadGenRun(BaseModel):
    run_id: str
    config: LeadGenFilter
    status: LeadGenRunStatus
    results_count: int = 0
    started_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None


class LeadSegment(BaseModel):
    segment_id: str
    name: str
    source_run_id: str
    lead_ids: list[str]
    created_at: str = Field(default_factory=now_iso)


class CampaignSettings(BaseModel):
    # Make campaign behavior UI-driven and explicit.
    call_window_tz: str = "America/New_York"
    call_window_start_hour: int = 9
    call_window_end_hour: int = 17
    max_retries_per_lead: int = 2

    # Assignment rules (minimal now; extensible later).
    assignment_strategy: Literal["round_robin", "single_agent"] = "single_agent"


class Campaign(BaseModel):
    campaign_id: str
    name: str
    status: CampaignStatus = "draft"

    # Campaign pulls from a segment OR a filter definition.
    segment_id: Optional[str] = None
    lead_filters: Optional[LeadGenFilter] = None

    agent_id: Optional[str] = None
    settings: CampaignSettings = Field(default_factory=CampaignSettings)

    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)


class AgentConfig(BaseModel):
    # Keep it declarative; UI can drive these knobs.
    model: str = "gpt-4o-realtime"
    temperature: float = 0.4
    max_tokens: int = 800
    system_prompt: str = ""
    voice_id: Optional[str] = None

    retry_attempts: int = 2
    cooldown_minutes: int = 10

    # Bridge to the voice-agent service (e.g. 'outbound', 'assistant')
    voice_agent_key: Optional[str] = "outbound"


class AgentStats(BaseModel):
    total_calls: int = 0
    success_rate: float = 0.0
    avg_call_duration: float = 0.0
    leads_processed: int = 0
    conversion_rate: float = 0.0


class Agent(BaseModel):
    agent_id: str
    name: str
    type: AgentType = "caller"
    status: AgentStatus = "active"
    version: str = "v1"
    config: AgentConfig = Field(default_factory=AgentConfig)
    stats: AgentStats = Field(default_factory=AgentStats)
    last_active: str = Field(default_factory=now_iso)


class CallAttempt(BaseModel):
    call_attempt_id: str
    campaign_id: str
    lead_id: str
    agent_id: str

    # Shared external identifier from Twilio.
    call_sid: Optional[str] = None

    to_number: str
    from_number: Optional[str] = None

    status: CallAttemptStatus = "queued"
    started_at: str = Field(default_factory=now_iso)
    ended_at: Optional[str] = None
    duration_seconds: Optional[int] = None
    recording_url: Optional[str] = None
    error: Optional[str] = None

    metadata: dict[str, Any] = Field(default_factory=dict)


class CallResult(BaseModel):
    # CallResult is intentionally separate from CallAttempt so we can guarantee
    # "every attempt yields a result record" even if the attempt fails early.
    call_result_id: str
    call_attempt_id: str
    campaign_id: str
    lead_id: str
    agent_id: str
    call_sid: Optional[str] = None

    outcome: Literal[
        "connected",
        "voicemail",
        "no_answer",
        "busy",
        "failed",
        "canceled",
        "unknown",
    ] = "unknown"

    finished_at: str = Field(default_factory=now_iso)
    summary: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Event(BaseModel):
    event_id: str
    ts: str = Field(default_factory=now_iso)
    type: EventType

    # Correlation across systems; always present in the API layer.
    correlation_id: str

    # Optional cross-links (nullable by design).
    campaign_id: Optional[str] = None
    lead_id: Optional[str] = None
    agent_id: Optional[str] = None
    call_attempt_id: Optional[str] = None
    call_sid: Optional[str] = None
    run_id: Optional[str] = None

    # Append-only payloads:
    raw: dict[str, Any] = Field(default_factory=dict)
    normalized: dict[str, Any] = Field(default_factory=dict)








