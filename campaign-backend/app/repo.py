from __future__ import annotations

from typing import Any, Optional

import sqlite3

from .db import jdump, jload
from .models import (
    Agent,
    AgentConfig,
    AgentStats,
    CallAttempt,
    CallResult,
    Campaign,
    CampaignSettings,
    Event,
    Lead,
    LeadGenRun,
    LeadGenFilter,
    LeadSegment,
    now_iso,
)


# ============================================================================
# Helpers
# ============================================================================


def _row_to_campaign(r: sqlite3.Row) -> Campaign:
    return Campaign(
        campaign_id=r["campaign_id"],
        name=r["name"],
        status=r["status"],
        segment_id=r["segment_id"],
        lead_filters=(LeadGenFilter.model_validate(jload(r["lead_filters_json"])) if r["lead_filters_json"] else None),
        agent_id=r["agent_id"],
        settings=CampaignSettings.model_validate(jload(r["settings_json"]) or {}),
        created_at=r["created_at"],
        updated_at=r["updated_at"],
    )


def _row_to_lead(r: sqlite3.Row) -> Lead:
    return Lead(
        lead_id=r["lead_id"],
        place_id=r["place_id"],
        name=r["name"],
        company=r["company"],
        phone=r["phone"],
        email=r["email"],
        website=r["website"],
        address=r["address"],
        status=r["status"],
        score=float(r["score"] or 0.0),
        campaign_id=r["campaign_id"],
        assigned_agent_id=r["assigned_agent_id"],
        notes=jload(r["notes_json"]) or [],
        timeline=jload(r["timeline_json"]) or [],
        metadata=jload(r["metadata_json"]) or {},
        created_at=r["created_at"],
        updated_at=r["updated_at"],
    )


def _row_to_agent(r: sqlite3.Row) -> Agent:
    return Agent(
        agent_id=r["agent_id"],
        name=r["name"],
        type=r["type"],
        status=r["status"],
        version=r["version"],
        config=AgentConfig.model_validate(jload(r["config_json"]) or {}),
        stats=AgentStats.model_validate(jload(r["stats_json"]) or {}),
        last_active=r["last_active"],
    )


def _row_to_run(r: sqlite3.Row) -> LeadGenRun:
    return LeadGenRun(
        run_id=r["run_id"],
        config=LeadGenFilter.model_validate(jload(r["config_json"]) or {}),
        status=r["status"],
        results_count=int(r["results_count"] or 0),
        started_at=r["started_at"],
        completed_at=r["completed_at"],
        error=r["error"],
    )


def _row_to_segment(r: sqlite3.Row) -> LeadSegment:
    return LeadSegment(
        segment_id=r["segment_id"],
        name=r["name"],
        source_run_id=r["source_run_id"],
        lead_ids=jload(r["lead_ids_json"]) or [],
        created_at=r["created_at"],
    )


def _row_to_call_attempt(r: sqlite3.Row) -> CallAttempt:
    return CallAttempt(
        call_attempt_id=r["call_attempt_id"],
        campaign_id=r["campaign_id"],
        lead_id=r["lead_id"],
        agent_id=r["agent_id"],
        call_sid=r["call_sid"],
        to_number=r["to_number"],
        from_number=r["from_number"],
        status=r["status"],
        started_at=r["started_at"],
        ended_at=r["ended_at"],
        duration_seconds=r["duration_seconds"],
        recording_url=r["recording_url"],
        error=r["error"],
        metadata=jload(r["metadata_json"]) or {},
    )


def _row_to_call_result(r: sqlite3.Row) -> CallResult:
    return CallResult(
        call_result_id=r["call_result_id"],
        call_attempt_id=r["call_attempt_id"],
        campaign_id=r["campaign_id"],
        lead_id=r["lead_id"],
        agent_id=r["agent_id"],
        call_sid=r["call_sid"],
        outcome=r["outcome"],
        finished_at=r["finished_at"],
        summary=r["summary"],
        metadata=jload(r["metadata_json"]) or {},
    )


# ============================================================================
# Campaigns
# ============================================================================


def list_campaigns(conn: sqlite3.Connection) -> list[Campaign]:
    rows = conn.execute("SELECT * FROM campaigns ORDER BY created_at DESC").fetchall()
    return [_row_to_campaign(r) for r in rows]


def get_campaign(conn: sqlite3.Connection, campaign_id: str) -> Optional[Campaign]:
    r = conn.execute("SELECT * FROM campaigns WHERE campaign_id=?", (campaign_id,)).fetchone()
    return _row_to_campaign(r) if r else None


def upsert_campaign(conn: sqlite3.Connection, c: Campaign) -> Campaign:
    now = now_iso()
    conn.execute(
        """
        INSERT INTO campaigns (
          campaign_id, name, status, segment_id, lead_filters_json, agent_id, settings_json, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(campaign_id) DO UPDATE SET
          name=excluded.name,
          status=excluded.status,
          segment_id=excluded.segment_id,
          lead_filters_json=excluded.lead_filters_json,
          agent_id=excluded.agent_id,
          settings_json=excluded.settings_json,
          updated_at=excluded.updated_at
        """,
        (
            c.campaign_id,
            c.name,
            c.status,
            c.segment_id,
            jdump(c.lead_filters.model_dump()) if c.lead_filters else None,
            c.agent_id,
            jdump(c.settings.model_dump()),
            c.created_at,
            now,
        ),
    )
    return get_campaign(conn, c.campaign_id) or c


def update_campaign_status(conn: sqlite3.Connection, campaign_id: str, status: str) -> Optional[Campaign]:
    conn.execute("UPDATE campaigns SET status=?, updated_at=? WHERE campaign_id=?", (status, now_iso(), campaign_id))
    return get_campaign(conn, campaign_id)


# ============================================================================
# Leads
# ============================================================================


def upsert_lead(conn: sqlite3.Connection, l: Lead) -> Lead:
    now = now_iso()
    conn.execute(
        """
        INSERT INTO leads (
          lead_id, place_id, name, company, phone, email, website, address,
          status, score, campaign_id, assigned_agent_id,
          notes_json, timeline_json, metadata_json,
          created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(lead_id) DO UPDATE SET
          place_id=excluded.place_id,
          name=excluded.name,
          company=excluded.company,
          phone=excluded.phone,
          email=excluded.email,
          website=excluded.website,
          address=excluded.address,
          status=excluded.status,
          score=excluded.score,
          campaign_id=excluded.campaign_id,
          assigned_agent_id=excluded.assigned_agent_id,
          notes_json=excluded.notes_json,
          timeline_json=excluded.timeline_json,
          metadata_json=excluded.metadata_json,
          updated_at=excluded.updated_at
        """,
        (
            l.lead_id,
            l.place_id,
            l.name,
            l.company,
            l.phone,
            l.email,
            l.website,
            l.address,
            l.status,
            l.score,
            l.campaign_id,
            l.assigned_agent_id,
            jdump(l.notes),
            jdump(l.timeline),
            jdump(l.metadata),
            l.created_at,
            now,
        ),
    )
    r = conn.execute("SELECT * FROM leads WHERE lead_id=?", (l.lead_id,)).fetchone()
    return _row_to_lead(r)


def get_lead(conn: sqlite3.Connection, lead_id: str) -> Optional[Lead]:
    r = conn.execute("SELECT * FROM leads WHERE lead_id=?", (lead_id,)).fetchone()
    return _row_to_lead(r) if r else None


def list_campaign_leads(conn: sqlite3.Connection, campaign_id: str) -> list[Lead]:
    rows = conn.execute("SELECT * FROM leads WHERE campaign_id=? ORDER BY created_at DESC", (campaign_id,)).fetchall()
    return [_row_to_lead(r) for r in rows]


def assign_leads_to_campaign(conn: sqlite3.Connection, lead_ids: list[str], campaign_id: str, agent_id: Optional[str]) -> None:
    now = now_iso()
    for lead_id in lead_ids:
        conn.execute(
            "UPDATE leads SET campaign_id=?, assigned_agent_id=?, updated_at=? WHERE lead_id=?",
            (campaign_id, agent_id, now, lead_id),
        )


# ============================================================================
# Agents
# ============================================================================


def list_agents(conn: sqlite3.Connection) -> list[Agent]:
    rows = conn.execute("SELECT * FROM agents ORDER BY name ASC").fetchall()
    return [_row_to_agent(r) for r in rows]


def get_agent(conn: sqlite3.Connection, agent_id: str) -> Optional[Agent]:
    r = conn.execute("SELECT * FROM agents WHERE agent_id=?", (agent_id,)).fetchone()
    return _row_to_agent(r) if r else None


def upsert_agent(conn: sqlite3.Connection, a: Agent) -> Agent:
    now = now_iso()
    conn.execute(
        """
        INSERT INTO agents (
          agent_id, name, type, status, version, config_json, stats_json, last_active, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(agent_id) DO UPDATE SET
          name=excluded.name,
          type=excluded.type,
          status=excluded.status,
          version=excluded.version,
          config_json=excluded.config_json,
          stats_json=excluded.stats_json,
          last_active=excluded.last_active,
          updated_at=excluded.updated_at
        """,
        (
            a.agent_id,
            a.name,
            a.type,
            a.status,
            a.version,
            jdump(a.config.model_dump()),
            jdump(a.stats.model_dump()),
            a.last_active,
            now,
            now,
        ),
    )
    return get_agent(conn, a.agent_id) or a


def toggle_agent(conn: sqlite3.Connection, agent_id: str) -> Optional[Agent]:
    agent = get_agent(conn, agent_id)
    if not agent:
        return None
    agent.status = "inactive" if agent.status == "active" else "active"
    return upsert_agent(conn, agent)


# ============================================================================
# LeadGen runs / results / segments
# ============================================================================


def create_run(conn: sqlite3.Connection, run: LeadGenRun) -> None:
    conn.execute(
        """
        INSERT INTO leadgen_runs(run_id, config_json, status, results_count, started_at, completed_at, error)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run.run_id,
            jdump(run.config.model_dump()),
            run.status,
            run.results_count,
            run.started_at,
            run.completed_at,
            run.error,
        ),
    )


def list_runs(conn: sqlite3.Connection) -> list[LeadGenRun]:
    rows = conn.execute("SELECT * FROM leadgen_runs ORDER BY started_at DESC").fetchall()
    return [_row_to_run(r) for r in rows]


def get_run(conn: sqlite3.Connection, run_id: str) -> Optional[LeadGenRun]:
    r = conn.execute("SELECT * FROM leadgen_runs WHERE run_id=?", (run_id,)).fetchone()
    return _row_to_run(r) if r else None


def update_run(conn: sqlite3.Connection, run: LeadGenRun) -> None:
    conn.execute(
        """
        UPDATE leadgen_runs
        SET status=?, results_count=?, completed_at=?, error=?
        WHERE run_id=?
        """,
        (run.status, run.results_count, run.completed_at, run.error, run.run_id),
    )


def add_run_result(conn: sqlite3.Connection, *, id: str, run_id: str, lead_id: str, row: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO leadgen_results(id, run_id, lead_id, business_name, address, phone, email, website, rating, review_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            id,
            run_id,
            lead_id,
            row.get("businessName") or row.get("business_name") or "",
            row.get("address"),
            row.get("phone"),
            row.get("email"),
            row.get("website"),
            row.get("rating"),
            row.get("reviewCount") or row.get("review_count"),
        ),
    )


def list_run_results(conn: sqlite3.Connection, run_id: str) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT * FROM leadgen_results WHERE run_id=? ORDER BY business_name ASC", (run_id,)).fetchall()
    results: list[dict[str, Any]] = []
    for r in rows:
        results.append(
            {
                "id": r["id"],
                "runId": r["run_id"],
                "businessName": r["business_name"],
                "address": r["address"],
                "phone": r["phone"],
                "email": r["email"],
                "website": r["website"],
                "rating": r["rating"],
                "reviewCount": r["review_count"],
                "leadId": r["lead_id"],
            }
        )
    return results


def create_segment(conn: sqlite3.Connection, seg: LeadSegment) -> None:
    conn.execute(
        """
        INSERT INTO segments(segment_id, name, source_run_id, lead_ids_json, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (seg.segment_id, seg.name, seg.source_run_id, jdump(seg.lead_ids), seg.created_at),
    )


def get_segment(conn: sqlite3.Connection, segment_id: str) -> Optional[LeadSegment]:
    r = conn.execute("SELECT * FROM segments WHERE segment_id=?", (segment_id,)).fetchone()
    return _row_to_segment(r) if r else None


def list_segments(conn: sqlite3.Connection, limit: int = 500) -> list[LeadSegment]:
    rows = conn.execute("SELECT * FROM segments ORDER BY created_at DESC LIMIT ?", (int(limit),)).fetchall()
    out: list[LeadSegment] = []
    for r in rows:
        seg = _row_to_segment(r)
        if seg:
            out.append(seg)
    return out


# ============================================================================
# Calls / events
# ============================================================================


def create_call_attempt(conn: sqlite3.Connection, ca: CallAttempt) -> None:
    conn.execute(
        """
        INSERT INTO call_attempts(
          call_attempt_id, campaign_id, lead_id, agent_id, call_sid,
          to_number, from_number, status, started_at, ended_at, duration_seconds,
          recording_url, error, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ca.call_attempt_id,
            ca.campaign_id,
            ca.lead_id,
            ca.agent_id,
            ca.call_sid,
            ca.to_number,
            ca.from_number,
            ca.status,
            ca.started_at,
            ca.ended_at,
            ca.duration_seconds,
            ca.recording_url,
            ca.error,
            jdump(ca.metadata),
        ),
    )


def update_call_attempt(conn: sqlite3.Connection, ca: CallAttempt) -> None:
    conn.execute(
        """
        UPDATE call_attempts
        SET call_sid=?, status=?, ended_at=?, duration_seconds=?, recording_url=?, error=?, metadata_json=?
        WHERE call_attempt_id=?
        """,
        (
            ca.call_sid,
            ca.status,
            ca.ended_at,
            ca.duration_seconds,
            ca.recording_url,
            ca.error,
            jdump(ca.metadata),
            ca.call_attempt_id,
        ),
    )


def get_call_attempt(conn: sqlite3.Connection, call_attempt_id: str) -> Optional[CallAttempt]:
    r = conn.execute("SELECT * FROM call_attempts WHERE call_attempt_id=?", (call_attempt_id,)).fetchone()
    return _row_to_call_attempt(r) if r else None


def find_call_attempt_by_call_sid(conn: sqlite3.Connection, call_sid: str) -> Optional[CallAttempt]:
    r = conn.execute("SELECT * FROM call_attempts WHERE call_sid=? ORDER BY started_at DESC LIMIT 1", (call_sid,)).fetchone()
    return _row_to_call_attempt(r) if r else None


def create_call_result(conn: sqlite3.Connection, cr: CallResult) -> None:
    conn.execute(
        """
        INSERT INTO call_results(
          call_result_id, call_attempt_id, campaign_id, lead_id, agent_id, call_sid,
          outcome, finished_at, summary, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cr.call_result_id,
            cr.call_attempt_id,
            cr.campaign_id,
            cr.lead_id,
            cr.agent_id,
            cr.call_sid,
            cr.outcome,
            cr.finished_at,
            cr.summary,
            jdump(cr.metadata),
        ),
    )


def get_call_result_by_attempt(conn: sqlite3.Connection, call_attempt_id: str) -> Optional[CallResult]:
    r = conn.execute("SELECT * FROM call_results WHERE call_attempt_id=? ORDER BY finished_at DESC LIMIT 1", (call_attempt_id,)).fetchone()
    return _row_to_call_result(r) if r else None


def append_event(conn: sqlite3.Connection, ev: Event) -> None:
    conn.execute(
        """
        INSERT INTO events(
          event_id, ts, type, correlation_id,
          campaign_id, lead_id, agent_id, call_attempt_id, call_sid, run_id,
          raw_json, normalized_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ev.event_id,
            ev.ts,
            ev.type,
            ev.correlation_id,
            ev.campaign_id,
            ev.lead_id,
            ev.agent_id,
            ev.call_attempt_id,
            ev.call_sid,
            ev.run_id,
            jdump(ev.raw),
            jdump(ev.normalized),
        ),
    )


def list_activity(conn: sqlite3.Connection, campaign_id: Optional[str] = None, limit: int = 200) -> list[dict[str, Any]]:
    if campaign_id:
        rows = conn.execute(
            "SELECT * FROM events WHERE campaign_id=? ORDER BY ts DESC LIMIT ?",
            (campaign_id, int(limit)),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM events ORDER BY ts DESC LIMIT ?", (int(limit),)).fetchall()

    out: list[dict[str, Any]] = []
    for r in rows:
        out.append(
            {
                "id": r["event_id"],
                "campaignId": r["campaign_id"],
                "type": r["type"],
                "timestamp": r["ts"],
                "correlationId": r["correlation_id"],
                "leadId": r["lead_id"],
                "agentId": r["agent_id"],
                "callSid": r["call_sid"],
                "raw": jload(r["raw_json"]) or {},
                "normalized": jload(r["normalized_json"]) or {},
            }
        )
    return out


