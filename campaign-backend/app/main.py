from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional
from urllib.parse import urlencode

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .db import connect, init_db, tx
from .ids import new_id
from .lead_engine_bridge import run_lead_engine
from .logging_utils import log
from .models import (
    Agent,
    AgentConfig,
    CallAttempt,
    CallResult,
    Campaign,
    CampaignSettings,
    Event,
    Lead,
    LeadGenFilter,
    LeadGenRun,
    LeadSegment,
    now_iso,
)
from .repo import (
    add_run_result,
    append_event,
    assign_leads_to_campaign,
    create_call_attempt,
    create_call_result,
    create_run,
    create_segment,
    get_agent,
    get_call_attempt,
    get_call_result_by_attempt,
    get_campaign,
    get_lead,
    get_run,
    get_segment,
    list_segments,
    list_activity,
    list_agents,
    list_campaign_leads,
    list_campaigns,
    list_run_results,
    list_runs,
    toggle_agent,
    update_call_attempt,
    update_campaign_status,
    update_run,
    upsert_agent,
    upsert_campaign,
    upsert_lead,
    find_call_attempt_by_call_sid,
)
from .twilio_bridge import TwilioConfigError, start_outbound_call


load_dotenv()

app = FastAPI(title="Campaign Orchestrator", version="0.1.0")

# CORS: allow frontend dev servers to call the API directly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:3000", "http://[::]:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

executor = ThreadPoolExecutor(max_workers=4)


def correlation_id_from_headers(x_correlation_id: Optional[str]) -> str:
    return (x_correlation_id or "").strip() or new_id("corr")


@app.middleware("http")
async def _correlation_middleware(request: Request, call_next):
    # Per-request DB connection (SQLite connections are not safely shareable across threads).
    db = connect()
    request.state.db = db
    corr = correlation_id_from_headers(request.headers.get("x-correlation-id"))
    request.state.correlation_id = corr
    try:
        resp = await call_next(request)
    except Exception as e:
        log("error", "request_failed", correlation_id=corr, path=str(request.url.path), error=str(e))
        resp = JSONResponse({"error": "Internal Server Error", "correlationId": corr}, status_code=500)
    finally:
        try:
            db.close()
        except Exception:
            pass
    resp.headers["X-Correlation-Id"] = corr
    return resp


def emit_event(
    *,
    conn,
    correlation_id: str,
    type: str,
    raw: dict[str, Any],
    normalized: dict[str, Any],
    campaign_id: Optional[str] = None,
    lead_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    call_attempt_id: Optional[str] = None,
    call_sid: Optional[str] = None,
    run_id: Optional[str] = None,
) -> None:
    ev = Event(
        event_id=new_id("evt"),
        type=type,
        correlation_id=correlation_id,
        campaign_id=campaign_id,
        lead_id=lead_id,
        agent_id=agent_id,
        call_attempt_id=call_attempt_id,
        call_sid=call_sid,
        run_id=run_id,
        raw=raw,
        normalized=normalized,
    )
    append_event(conn, ev)


def ensure_seed_data() -> None:
    # Seed a minimal outbound agent so the UI has something to bind to.
    c = connect()
    try:
        init_db(c)
        existing = list_agents(c)
        if existing:
            return

        a = Agent(
            agent_id=new_id("agent"),
            name="Outbound Caller (Nika)",
            type="caller",
            status="active",
            version="v1",
            config=AgentConfig(
                system_prompt="",
                voice_agent_key="outbound",
                temperature=0.4,
                max_tokens=800,
            ),
        )
        with tx(c):
            upsert_agent(c, a)
    finally:
        c.close()


@app.on_event("startup")
def _startup():
    c = connect()
    try:
        init_db(c)
    finally:
        c.close()
    ensure_seed_data()


# ============================================================================
# Schemas (frontend-driven config)
# ============================================================================


@app.get("/api/schemas/lead_filters")
def schema_lead_filters():
    return LeadGenFilter.model_json_schema()


@app.get("/api/schemas/agent_config")
def schema_agent_config():
    return AgentConfig.model_json_schema()


@app.get("/api/schemas/campaign_settings")
def schema_campaign_settings():
    return CampaignSettings.model_json_schema()


# ============================================================================
# Campaigns API (matches sunbeam-crm expectations)
# ============================================================================


# ============================================================================
# Segments API (for UI-driven campaign creation)
# ============================================================================


@app.get("/api/segments")
def api_list_segments(request: Request, limit: int = 500):
    conn = request.state.db
    segs = list_segments(conn, limit=limit)
    out: list[dict[str, Any]] = []
    for s in segs:
        out.append(
            {
                "id": s.segment_id,
                "name": s.name,
                "sourceRunId": s.source_run_id,
                "leadCount": len(s.lead_ids),
                "createdAt": s.created_at,
            }
        )
    return out


@app.get("/api/segments/{segment_id}")
def api_get_segment(segment_id: str, request: Request):
    conn = request.state.db
    s = get_segment(conn, segment_id)
    if not s:
        raise HTTPException(status_code=404, detail="Segment not found")
    return {
        "id": s.segment_id,
        "name": s.name,
        "sourceRunId": s.source_run_id,
        "leadIds": s.lead_ids,
        "leadCount": len(s.lead_ids),
        "createdAt": s.created_at,
    }



@app.get("/api/campaigns")
def api_list_campaigns(request: Request):
    conn = request.state.db
    camps = list_campaigns(conn)
    # Keep response shape compatible with CRM types.
    out = []
    for c in camps:
        leads_count = len(list_campaign_leads(conn, c.campaign_id))
        # Resolve segment and agent names
        seg_name = None
        if c.segment_id:
            seg = get_segment(conn, c.segment_id)
            if seg:
                seg_name = seg.name
        agent_name = None
        if c.agent_id:
            agent = get_agent(conn, c.agent_id)
            if agent:
                agent_name = agent.name
        out.append(
            {
                "id": c.campaign_id,
                "name": c.name,
                "status": c.status,
                "leadsCount": leads_count,
                "conversionRate": 0,
                "createdAt": c.created_at,
                "updatedAt": c.updated_at,
                "segmentId": c.segment_id,
                "segmentName": seg_name,
                "agentId": c.agent_id,
                "agentName": agent_name,
            }
        )
    return out


# NOTE: Static routes must come BEFORE parameterized routes like /api/campaigns/{campaign_id}
@app.get("/api/campaigns/kpi")
def api_campaign_kpis(request: Request):
    conn = request.state.db
    # Minimal KPI rollup.
    total_leads = conn.execute("SELECT COUNT(1) as c FROM leads").fetchone()["c"]
    total_calls = conn.execute("SELECT COUNT(1) as c FROM call_attempts").fetchone()["c"]
    return {
        "totalLeads": total_leads,
        "newLeadsToday": 0,
        "conversionRate": 0,
        "avgDealValue": 0,
        "callsMade": total_calls,
        "meetingsScheduled": 0,
    }


@app.get("/api/campaigns/activity")
def api_activity(request: Request, limit: int = 200):
    conn = request.state.db
    return _activity_to_crm(list_activity(conn, None, limit))


@app.post("/api/campaigns")
async def api_create_campaign(request: Request):
    conn = request.state.db
    corr = request.state.correlation_id
    body = await request.json()
    name = str(body.get("name") or "").strip()
    segment_id = body.get("segmentId")
    agent_id = body.get("agentId")

    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    c = Campaign(
        campaign_id=new_id("camp"),
        name=name,
        status="active",
        segment_id=segment_id,
        agent_id=agent_id,
    )

    with tx(conn):
        upsert_campaign(conn, c)

        # If a segment is provided, assign those leads immediately.
        if segment_id:
            seg = get_segment(conn, segment_id)
            if seg:
                assign_leads_to_campaign(conn, seg.lead_ids, c.campaign_id, agent_id)

        emit_event(
            conn=conn,
            correlation_id=corr,
            type="campaign.created",
            campaign_id=c.campaign_id,
            raw={"body": body},
            normalized={"campaign_id": c.campaign_id, "name": c.name, "segment_id": segment_id, "agent_id": agent_id},
        )

    # Resolve segment and agent names for response
    seg_name = None
    if segment_id:
        seg = get_segment(conn, segment_id)
        if seg:
            seg_name = seg.name
    agent_obj = get_agent(conn, agent_id) if agent_id else None
    agent_name_resolved = agent_obj.name if agent_obj else None

    return {
        "id": c.campaign_id,
        "name": c.name,
        "status": c.status,
        "leadsCount": 0,
        "conversionRate": 0,
        "createdAt": c.created_at,
        "updatedAt": c.updated_at,
        "segmentId": segment_id,
        "segmentName": seg_name,
        "agentId": agent_id,
        "agentName": agent_name_resolved,
    }


@app.get("/api/campaigns/{campaign_id}")
def api_get_campaign(campaign_id: str, request: Request):
    conn = request.state.db
    c = get_campaign(conn, campaign_id)
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")
    leads_count = len(list_campaign_leads(conn, c.campaign_id))
    # Resolve segment and agent names
    seg_name = None
    if c.segment_id:
        seg = get_segment(conn, c.segment_id)
        if seg:
            seg_name = seg.name
    agent_name = None
    if c.agent_id:
        agent = get_agent(conn, c.agent_id)
        if agent:
            agent_name = agent.name
    return {
        "id": c.campaign_id,
        "name": c.name,
        "status": c.status,
        "leadsCount": leads_count,
        "conversionRate": 0,
        "createdAt": c.created_at,
        "updatedAt": c.updated_at,
        "segmentId": c.segment_id,
        "segmentName": seg_name,
        "agentId": c.agent_id,
        "agentName": agent_name,
    }


@app.put("/api/campaigns/{campaign_id}/status")
async def api_update_campaign_status(campaign_id: str, request: Request):
    conn = request.state.db
    corr = request.state.correlation_id
    body = await request.json()
    status = body.get("status")
    if status not in ("active", "paused", "completed", "draft"):
        raise HTTPException(status_code=400, detail="Invalid status")
    with tx(conn):
        c = update_campaign_status(conn, campaign_id, status)
        if not c:
            raise HTTPException(status_code=404, detail="Campaign not found")
        emit_event(
            conn=conn,
            correlation_id=corr,
            type="campaign.status.updated",
            campaign_id=campaign_id,
            raw={"body": body},
            normalized={"campaign_id": campaign_id, "status": status},
        )
    # Resolve segment and agent names
    seg_name = None
    if c.segment_id:
        seg = get_segment(conn, c.segment_id)
        if seg:
            seg_name = seg.name
    agent_name = None
    if c.agent_id:
        agent = get_agent(conn, c.agent_id)
        if agent:
            agent_name = agent.name
    return {
        "id": c.campaign_id,
        "name": c.name,
        "status": c.status,
        "leadsCount": len(list_campaign_leads(conn, c.campaign_id)),
        "conversionRate": 0,
        "createdAt": c.created_at,
        "updatedAt": c.updated_at,
        "segmentId": c.segment_id,
        "segmentName": seg_name,
        "agentId": c.agent_id,
        "agentName": agent_name,
    }


@app.get("/api/campaigns/{campaign_id}/leads")
def api_campaign_leads(campaign_id: str, request: Request):
    conn = request.state.db
    leads = list_campaign_leads(conn, campaign_id)
    out = []
    for l in leads:
        out.append(
            {
                "id": l.lead_id,
                "name": l.name,
                "email": l.email or "",
                "phone": l.phone or "",
                "company": l.company or l.name,
                "status": l.status,
                "score": l.score,
                "campaignId": l.campaign_id or "",
                "assignedTo": l.assigned_agent_id or "",
                "createdAt": l.created_at,
                "lastContact": l.updated_at,
                "value": 0,
                "notes": l.notes,
                "timeline": l.timeline,
            }
        )
    return out


@app.get("/api/campaigns/{campaign_id}/activity")
def api_campaign_activity(campaign_id: str, request: Request, limit: int = 200):
    conn = request.state.db
    return _activity_to_crm(list_activity(conn, campaign_id, limit))


def _activity_to_crm(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # CRM expects CampaignActivity[]; we project from events.
    out = []
    for e in events:
        raw = e.get("raw") or {}
        normalized = e.get("normalized") or {}
        lead_name = normalized.get("lead_name") or raw.get("lead_name") or "Unknown lead"
        lead_phone = normalized.get("lead_phone") or raw.get("lead_phone") or ""
        agent_name = normalized.get("agent_name") or raw.get("agent_name") or "Agent"
        crm_type = "call_started"
        if e["type"] in ("call.result.created", "call.attempt.updated"):
            crm_type = "call_ended"
        if e["type"] == "call.result.created" and normalized.get("outcome") == "connected":
            crm_type = "call_success"
        if e["type"] == "call.result.created" and normalized.get("outcome") in ("failed", "no_answer", "busy"):
            crm_type = "call_failed"

        out.append(
            {
                "id": e["id"],
                "campaignId": e.get("campaignId") or "",
                "type": crm_type,
                "leadName": lead_name,
                "leadPhone": lead_phone,
                "agentName": agent_name,
                "timestamp": e["timestamp"],
                "duration": normalized.get("duration_seconds"),
                "outcome": normalized.get("outcome"),
                "notes": normalized.get("summary"),
            }
        )
    return out


# ============================================================================
# Leads API
# ============================================================================


@app.put("/api/leads/{lead_id}")
async def api_update_lead(lead_id: str, request: Request):
    conn = request.state.db
    corr = request.state.correlation_id
    l = get_lead(conn, lead_id)
    if not l:
        raise HTTPException(status_code=404, detail="Lead not found")
    patch = await request.json()

    # Very small, explicit patch surface (safe defaults).
    for k in ("status", "score", "assignedTo", "campaignId"):
        if k in patch:
            if k == "assignedTo":
                l.assigned_agent_id = patch[k] or None
            elif k == "campaignId":
                l.campaign_id = patch[k] or None
            else:
                setattr(l, k if k != "status" else "status", patch[k])

    l.updated_at = now_iso()
    with tx(conn):
        l2 = upsert_lead(conn, l)
        emit_event(
            conn=conn,
            correlation_id=corr,
            type="lead.updated",
            campaign_id=l2.campaign_id,
            lead_id=l2.lead_id,
            raw={"patch": patch},
            normalized={"lead_id": l2.lead_id, "status": l2.status, "score": l2.score},
        )
    return {
        "id": l2.lead_id,
        "name": l2.name,
        "email": l2.email or "",
        "phone": l2.phone or "",
        "company": l2.company or l2.name,
        "status": l2.status,
        "score": l2.score,
        "campaignId": l2.campaign_id or "",
        "assignedTo": l2.assigned_agent_id or "",
        "createdAt": l2.created_at,
        "lastContact": l2.updated_at,
        "value": 0,
        "notes": l2.notes,
        "timeline": l2.timeline,
    }


# ============================================================================
# LeadGen API
# ============================================================================


def _run_leadgen_job(*, run_id: str, corr: str) -> None:
    conn = connect()
    try:
        run = get_run(conn, run_id)
        if not run:
            return

        with tx(conn):
            emit_event(
                conn=conn,
                correlation_id=corr,
                type="leadgen.run.started",
                run_id=run_id,
                raw={"run_id": run_id, "config": run.config.model_dump()},
                normalized={"run_id": run_id},
            )

        try:
            results = run_lead_engine(run.config.model_dump())
            # Persist results and create canonical Leads (campaign_id remains null until segment/campaign assignment).
            with tx(conn):
                for r in results:
                    lead_id = new_id("lead")
                    lead = Lead(
                        lead_id=lead_id,
                        place_id=r.get("place_id"),
                        name=r.get("name") or "",
                        company=r.get("name") or "",
                        phone=(r.get("phone") if run.config.include_phones else None),
                        email=(r.get("email") if run.config.include_emails else None),
                        website=r.get("website"),
                        address=r.get("address"),
                        status="new",
                        score=0.0,
                        metadata={"leadgen": {"run_id": run_id, "raw": r.get("raw")}},
                    )
                    upsert_lead(conn, lead)
                    add_run_result(
                        conn,
                        id=new_id("lgr"),
                        run_id=run_id,
                        lead_id=lead_id,
                        row={
                            "businessName": r.get("name"),
                            "address": r.get("address"),
                            "phone": lead.phone,
                            "email": lead.email,
                            "website": r.get("website"),
                            "rating": r.get("rating"),
                            "reviewCount": r.get("review_count"),
                        },
                    )

                run.status = "completed"
                run.completed_at = now_iso()
                run.results_count = len(results)
                update_run(conn, run)

                emit_event(
                    conn=conn,
                    correlation_id=corr,
                    type="leadgen.run.completed",
                    run_id=run_id,
                    raw={"run_id": run_id},
                    normalized={"run_id": run_id, "results_count": len(results)},
                )
        except Exception as e:
            with tx(conn):
                run.status = "failed"
                run.completed_at = now_iso()
                run.error = str(e)
                update_run(conn, run)
                emit_event(
                    conn=conn,
                    correlation_id=corr,
                    type="leadgen.run.failed",
                    run_id=run_id,
                    raw={"error": str(e)},
                    normalized={"run_id": run_id, "error": str(e)},
                )
    finally:
        conn.close()


@app.post("/api/leadgen/run")
async def api_leadgen_run(request: Request):
    conn = request.state.db
    corr = request.state.correlation_id
    body = await request.json()

    # Map CRM config keys → canonical keys.
    cfg = LeadGenFilter(
        query=str(body.get("query") or "").strip(),
        location=str(body.get("location") or "").strip(),
        radius_miles=int(body.get("radius") or 25),
        max_results=int(body.get("maxResults") or 100),
        max_pages=int(body.get("maxPages") or 3),
        no_crawl=bool(body.get("noCrawl") or False),
        include_emails=bool(body.get("includeEmails") if body.get("includeEmails") is not None else True),
        include_phones=bool(body.get("includePhones") if body.get("includePhones") is not None else True),
    )

    run = LeadGenRun(
        run_id=new_id("run"),
        config=cfg,
        status="running",
        results_count=0,
        started_at=now_iso(),
    )

    with tx(conn):
        create_run(conn, run)

    # Start background job (thread pool).
    executor.submit(_run_leadgen_job, run_id=run.run_id, corr=corr)

    return {
        "id": run.run_id,
        "config": {
            "query": cfg.query,
            "location": cfg.location,
            "radius": cfg.radius_miles,
            "maxResults": cfg.max_results,
            "maxPages": cfg.max_pages,
            "noCrawl": cfg.no_crawl,
            "includeEmails": cfg.include_emails,
            "includePhones": cfg.include_phones,
        },
        "status": run.status,
        "resultsCount": 0,
        "startedAt": run.started_at,
        "completedAt": None,
        "error": None,
    }


@app.get("/api/leadgen/runs")
def api_leadgen_runs(request: Request):
    conn = request.state.db
    runs = list_runs(conn)
    out = []
    for r in runs:
        cfg = r.config
        out.append(
            {
                "id": r.run_id,
                "config": {
                    "query": cfg.query,
                    "location": cfg.location,
                    "radius": cfg.radius_miles,
                    "maxResults": cfg.max_results,
                    "maxPages": cfg.max_pages,
                    "noCrawl": cfg.no_crawl,
                    "includeEmails": cfg.include_emails,
                    "includePhones": cfg.include_phones,
                },
                "status": r.status,
                "resultsCount": r.results_count,
                "startedAt": r.started_at,
                "completedAt": r.completed_at,
                "error": r.error,
            }
        )
    return out


@app.get("/api/leadgen/runs/{run_id}")
def api_leadgen_run(run_id: str, request: Request):
    conn = request.state.db
    r = get_run(conn, run_id)
    if not r:
        raise HTTPException(status_code=404, detail="Run not found")
    cfg = r.config
    return {
        "id": r.run_id,
        "config": {
            "query": cfg.query,
            "location": cfg.location,
            "radius": cfg.radius_miles,
            "maxResults": cfg.max_results,
            "maxPages": cfg.max_pages,
            "noCrawl": cfg.no_crawl,
            "includeEmails": cfg.include_emails,
            "includePhones": cfg.include_phones,
        },
        "status": r.status,
        "resultsCount": r.results_count,
        "startedAt": r.started_at,
        "completedAt": r.completed_at,
        "error": r.error,
    }


@app.get("/api/leadgen/runs/{run_id}/results")
def api_leadgen_results(run_id: str, request: Request):
    conn = request.state.db
    return list_run_results(conn, run_id)


@app.post("/api/leadgen/runs/{run_id}/save-segment")
async def api_leadgen_save_segment(run_id: str, request: Request):
    conn = request.state.db
    corr = request.state.correlation_id
    body = await request.json()
    name = str(body.get("name") or f"Segment {run_id}").strip()
    run = get_run(conn, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    results = list_run_results(conn, run_id)
    lead_ids = [r["leadId"] for r in results if r.get("leadId")]
    seg = LeadSegment(segment_id=new_id("seg"), name=name, source_run_id=run_id, lead_ids=lead_ids)
    with tx(conn):
        create_segment(conn, seg)
        emit_event(
            conn=conn,
            correlation_id=corr,
            type="segment.created",
            run_id=run_id,
            raw={"name": name},
            normalized={"segment_id": seg.segment_id, "run_id": run_id, "lead_count": len(lead_ids)},
        )
    return {"segmentId": seg.segment_id}


# ============================================================================
# Agents API
# ============================================================================


@app.get("/api/agents")
def api_agents(request: Request):
    conn = request.state.db
    agents = list_agents(conn)
    out = []
    for a in agents:
        out.append(
            {
                "id": a.agent_id,
                "name": a.name,
                "type": a.type,
                "status": a.status,
                "version": a.version,
                "config": {
                    "model": a.config.model,
                    "temperature": a.config.temperature,
                    "maxTokens": a.config.max_tokens,
                    "systemPrompt": a.config.system_prompt,
                    "voiceId": a.config.voice_id,
                    "retryAttempts": a.config.retry_attempts,
                    "cooldownMinutes": a.config.cooldown_minutes,
                },
                "stats": {
                    "totalCalls": a.stats.total_calls,
                    "successRate": a.stats.success_rate,
                    "avgCallDuration": a.stats.avg_call_duration,
                    "leadsProcessed": a.stats.leads_processed,
                    "conversionRate": a.stats.conversion_rate,
                },
                "lastActive": a.last_active,
            }
        )
    return out


@app.get("/api/agents/{agent_id}")
def api_agent(agent_id: str, request: Request):
    conn = request.state.db
    a = get_agent(conn, agent_id)
    if not a:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {
        "id": a.agent_id,
        "name": a.name,
        "type": a.type,
        "status": a.status,
        "version": a.version,
        "config": {
            "model": a.config.model,
            "temperature": a.config.temperature,
            "maxTokens": a.config.max_tokens,
            "systemPrompt": a.config.system_prompt,
            "voiceId": a.config.voice_id,
            "retryAttempts": a.config.retry_attempts,
            "cooldownMinutes": a.config.cooldown_minutes,
        },
        "stats": {
            "totalCalls": a.stats.total_calls,
            "successRate": a.stats.success_rate,
            "avgCallDuration": a.stats.avg_call_duration,
            "leadsProcessed": a.stats.leads_processed,
            "conversionRate": a.stats.conversion_rate,
        },
        "lastActive": a.last_active,
    }


@app.put("/api/agents/{agent_id}/config")
async def api_agent_config(agent_id: str, request: Request):
    conn = request.state.db
    body = await request.json()
    a = get_agent(conn, agent_id)
    if not a:
        raise HTTPException(status_code=404, detail="Agent not found")
    a.config.model = body.get("model", a.config.model)
    a.config.temperature = float(body.get("temperature", a.config.temperature))
    a.config.max_tokens = int(body.get("maxTokens", a.config.max_tokens))
    a.config.system_prompt = body.get("systemPrompt", a.config.system_prompt)
    a.config.voice_id = body.get("voiceId", a.config.voice_id)
    a.config.retry_attempts = int(body.get("retryAttempts", a.config.retry_attempts))
    a.config.cooldown_minutes = int(body.get("cooldownMinutes", a.config.cooldown_minutes))
    with tx(conn):
        upsert_agent(conn, a)
    return api_agent(agent_id)


@app.post("/api/agents/{agent_id}/toggle")
def api_toggle_agent(agent_id: str, request: Request):
    conn = request.state.db
    a = toggle_agent(conn, agent_id)
    if not a:
        raise HTTPException(status_code=404, detail="Agent not found")
    return api_agent(agent_id, request)


@app.get("/api/agents/{agent_id}/performance")
def api_agent_performance(agent_id: str, days: int = 7):
    # Minimal stub; can be backed by events later.
    conn = connect()
    try:
        if not get_agent(conn, agent_id):
            raise HTTPException(status_code=404, detail="Agent not found")
    finally:
        conn.close()
    out = []
    for i in range(max(1, int(days))):
        out.append({"date": f"day-{i+1}", "calls": 0, "success": 0, "conversions": 0})
    return out


# ============================================================================
# Campaign execution (voice agent + Twilio)
# ============================================================================


@app.post("/api/campaigns/{campaign_id}/execute")
async def api_execute_campaign(campaign_id: str, request: Request):
    conn = request.state.db
    corr = request.state.correlation_id
    c = get_campaign(conn, campaign_id)
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if c.status != "active":
        raise HTTPException(status_code=400, detail="Campaign must be active to execute")
    if not c.agent_id:
        raise HTTPException(status_code=400, detail="Campaign missing agentId")

    agent = get_agent(conn, c.agent_id)
    if not agent or agent.status != "active":
        raise HTTPException(status_code=400, detail="Assigned agent not active")

    leads = list_campaign_leads(conn, campaign_id)
    targets = [l for l in leads if (l.status == "new" and l.phone)]

    voice_base = os.getenv("VOICE_AGENT_BASE_URL", "").rstrip("/")
    if not voice_base:
        raise HTTPException(status_code=400, detail="VOICE_AGENT_BASE_URL not configured")

    started: list[dict[str, Any]] = []

    for l in targets:
        call_attempt_id = new_id("call")
        ca = CallAttempt(
            call_attempt_id=call_attempt_id,
            campaign_id=campaign_id,
            lead_id=l.lead_id,
            agent_id=agent.agent_id,
            to_number=l.phone or "",
            from_number=os.getenv("TWILIO_FROM_NUMBER") or None,
            status="queued",
            metadata={"voice_agent_key": agent.config.voice_agent_key},
        )

        # Build TwiML URL on the voice-agent service. We pass identifiers through so the
        # /twilio/stream customParameters contains campaign/lead/attempt IDs.
        twiml_url = (
            f"{voice_base}/twilio/outbound?"
            + urlencode(
                {
                    "agent": agent.config.voice_agent_key or "outbound",
                    "campaign_id": campaign_id,
                    "lead_id": l.lead_id,
                    "call_attempt_id": call_attempt_id,
                    "correlation_id": corr,
                }
            )
        )

        # Status callback to THIS backend.
        # NOTE: In production, this URL should be public + https.
        callback_base = str(request.base_url).rstrip("/")
        status_cb = (
            f"{callback_base}/api/webhooks/twilio/call-status?"
            + urlencode(
                {
                    "campaign_id": campaign_id,
                    "lead_id": l.lead_id,
                    "agent_id": agent.agent_id,
                    "call_attempt_id": call_attempt_id,
                    "correlation_id": corr,
                }
            )
        )

        with tx(conn):
            create_call_attempt(conn, ca)
            emit_event(
                conn=conn,
                correlation_id=corr,
                type="call.attempt.created",
                campaign_id=campaign_id,
                lead_id=l.lead_id,
                agent_id=agent.agent_id,
                call_attempt_id=call_attempt_id,
                raw={"to": ca.to_number, "twiml_url": twiml_url},
                normalized={"lead_name": l.name, "lead_phone": l.phone, "agent_name": agent.name},
            )

        try:
            call_sid = start_outbound_call(
                to_number=ca.to_number,
                twiml_url=twiml_url,
                status_callback_url=status_cb,
            )
            ca.call_sid = call_sid
            ca.status = "initiated"
            with tx(conn):
                update_call_attempt(conn, ca)
                emit_event(
                    conn=conn,
                    correlation_id=corr,
                    type="call.attempt.updated",
                    campaign_id=campaign_id,
                    lead_id=l.lead_id,
                    agent_id=agent.agent_id,
                    call_attempt_id=call_attempt_id,
                    call_sid=call_sid,
                    raw={"status": "initiated"},
                    normalized={"outcome": None},
                )
            started.append({"callAttemptId": call_attempt_id, "callSid": call_sid, "leadId": l.lead_id})
        except TwilioConfigError as e:
            # Still persist a result record so this attempt isn't lost.
            ca.status = "failed"
            ca.error = str(e)
            with tx(conn):
                update_call_attempt(conn, ca)
                _ensure_result_for_attempt(
                    conn=conn,
                    corr=corr,
                    ca=ca,
                    outcome="failed",
                    summary=str(e),
                    lead_name=l.name,
                    lead_phone=l.phone,
                    agent_name=agent.name,
                )
            started.append({"callAttemptId": call_attempt_id, "error": str(e), "leadId": l.lead_id})
        except Exception as e:
            ca.status = "failed"
            ca.error = str(e)
            with tx(conn):
                update_call_attempt(conn, ca)
                _ensure_result_for_attempt(
                    conn=conn,
                    corr=corr,
                    ca=ca,
                    outcome="failed",
                    summary=str(e),
                    lead_name=l.name,
                    lead_phone=l.phone,
                    agent_name=agent.name,
                )
            started.append({"callAttemptId": call_attempt_id, "error": str(e), "leadId": l.lead_id})

    with tx(conn):
        emit_event(
            conn=conn,
            correlation_id=corr,
            type="campaign.executed",
            campaign_id=campaign_id,
            raw={"started": started},
            normalized={"campaign_id": campaign_id, "attempts_started": len(started)},
        )
    return {"ok": True, "started": started}


def _ensure_result_for_attempt(
    *,
    conn,
    corr: str,
    ca: CallAttempt,
    outcome: str,
    summary: Optional[str] = None,
    extra: Optional[dict[str, Any]] = None,
    lead_name: Optional[str] = None,
    lead_phone: Optional[str] = None,
    agent_name: Optional[str] = None,
) -> CallResult:
    existing = get_call_result_by_attempt(conn, ca.call_attempt_id)
    if existing:
        return existing
    cr = CallResult(
        call_result_id=new_id("cres"),
        call_attempt_id=ca.call_attempt_id,
        campaign_id=ca.campaign_id,
        lead_id=ca.lead_id,
        agent_id=ca.agent_id,
        call_sid=ca.call_sid,
        outcome=outcome,  # type: ignore[arg-type]
        summary=summary,
        metadata=extra or {},
    )
    create_call_result(conn, cr)
    emit_event(
        conn=conn,
        correlation_id=corr,
        type="call.result.created",
        campaign_id=ca.campaign_id,
        lead_id=ca.lead_id,
        agent_id=ca.agent_id,
        call_attempt_id=ca.call_attempt_id,
        call_sid=ca.call_sid,
        raw={"summary": summary, "metadata": cr.metadata},
        normalized={
            "outcome": cr.outcome,
            "summary": summary,
            "lead_name": lead_name,
            "lead_phone": lead_phone,
            "agent_name": agent_name,
        },
    )
    return cr


# ============================================================================
# Webhooks (Twilio + voice agent)
# ============================================================================


@app.post("/api/webhooks/twilio/call-status")
async def twilio_call_status_webhook(
    request: Request,
    campaign_id: Optional[str] = None,
    lead_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    call_attempt_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
):
    corr = (correlation_id or request.state.correlation_id) if hasattr(request.state, "correlation_id") else (correlation_id or new_id("corr"))
    conn = request.state.db

    # Twilio sends application/x-www-form-urlencoded by default.
    form = await request.form()
    payload = dict(form)

    call_sid = payload.get("CallSid")
    status = payload.get("CallStatus") or payload.get("CallStatus".lower())
    duration = payload.get("CallDuration")
    recording_url = payload.get("RecordingUrl")

    ca = get_call_attempt(conn, call_attempt_id) if call_attempt_id else (find_call_attempt_by_call_sid(conn, call_sid) if call_sid else None)
    if not ca:
        # Still record event to avoid swallowed failures.
        with tx(conn):
            emit_event(
                correlation_id=corr,
                type="error",
                campaign_id=campaign_id,
                lead_id=lead_id,
                agent_id=agent_id,
                call_attempt_id=call_attempt_id,
                call_sid=call_sid,
                raw={"twilio": payload},
                normalized={"error": "call_attempt_not_found"},
            )
        return {"ok": True}

    # Map Twilio statuses into our attempt + outcome.
    mapped = {
        "queued": "queued",
        "initiated": "initiated",
        "ringing": "ringing",
        "in-progress": "in_progress",
        "completed": "completed",
        "busy": "busy",
        "no-answer": "no_answer",
        "failed": "failed",
        "canceled": "canceled",
    }
    ca.call_sid = call_sid or ca.call_sid
    ca.status = mapped.get(str(status), ca.status)
    if duration is not None:
        try:
            ca.duration_seconds = int(duration)
        except Exception:
            pass
    if recording_url:
        ca.recording_url = recording_url
    if ca.status in ("completed", "failed", "no_answer", "busy", "canceled"):
        ca.ended_at = now_iso()

    with tx(conn):
        update_call_attempt(conn, ca)
        emit_event(
            conn=conn,
            correlation_id=corr,
            type="call.attempt.updated",
            campaign_id=ca.campaign_id,
            lead_id=ca.lead_id,
            agent_id=ca.agent_id,
            call_attempt_id=ca.call_attempt_id,
            call_sid=ca.call_sid,
            raw={"twilio": payload},
            normalized={"status": ca.status, "duration_seconds": ca.duration_seconds},
        )

        # Ensure result exists on terminal statuses.
        if ca.status in ("completed", "failed", "no_answer", "busy", "canceled"):
            outcome = "unknown"
            if ca.status == "completed":
                outcome = "connected"
            if ca.status in ("no_answer", "busy", "failed", "canceled"):
                outcome = ca.status
            # Look up lead and agent for event normalization
            lead = get_lead(conn, ca.lead_id) if ca.lead_id else None
            agent = get_agent(conn, ca.agent_id) if ca.agent_id else None
            _ensure_result_for_attempt(
                conn=conn,
                corr=corr,
                ca=ca,
                outcome=outcome,
                lead_name=lead.name if lead else None,
                lead_phone=lead.phone if lead else None,
                agent_name=agent.name if agent else None,
            )

    return {"ok": True}


@app.post("/api/webhooks/voice-agent/tool-log")
async def voice_agent_tool_log(request: Request):
    corr = request.state.correlation_id
    conn = request.state.db
    body = await request.json()

    # We expect voice-agent to send call_sid when possible.
    call_sid = body.get("callSid") or body.get("call_sid") or body.get("sessionId")
    tool = body.get("toolName") or body.get("tool_name")
    agent_name = body.get("agentName") or body.get("agent_name")

    with tx(conn):
        emit_event(
            conn=conn,
            correlation_id=corr,
            type="voice_agent.tool_log",
            call_sid=call_sid,
            raw=body,
            normalized={"tool": tool, "agent_name": agent_name},
        )
    return {"ok": True}


