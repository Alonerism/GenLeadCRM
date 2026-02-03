from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from typing import Any, Iterator, Optional


def _db_path() -> str:
    return os.getenv("CAMPAIGN_DB_PATH", "./campaign.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


@contextmanager
def tx(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    try:
        conn.execute("BEGIN;")
        yield conn
        conn.execute("COMMIT;")
    except Exception:
        conn.execute("ROLLBACK;")
        raise


def jdump(v: Any) -> str:
    return json.dumps(v, ensure_ascii=False, separators=(",", ":"))


def jload(s: Optional[str]) -> Any:
    if not s:
        return None
    return json.loads(s)


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS campaigns (
          campaign_id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          status TEXT NOT NULL,
          segment_id TEXT,
          lead_filters_json TEXT,
          agent_id TEXT,
          settings_json TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS leads (
          lead_id TEXT PRIMARY KEY,
          place_id TEXT,
          name TEXT NOT NULL,
          company TEXT,
          phone TEXT,
          email TEXT,
          website TEXT,
          address TEXT,
          status TEXT NOT NULL,
          score REAL NOT NULL,
          campaign_id TEXT,
          assigned_agent_id TEXT,
          notes_json TEXT NOT NULL,
          timeline_json TEXT NOT NULL,
          metadata_json TEXT NOT NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_leads_campaign ON leads(campaign_id);

        CREATE TABLE IF NOT EXISTS agents (
          agent_id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          type TEXT NOT NULL,
          status TEXT NOT NULL,
          version TEXT NOT NULL,
          config_json TEXT NOT NULL,
          stats_json TEXT NOT NULL,
          last_active TEXT NOT NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS leadgen_runs (
          run_id TEXT PRIMARY KEY,
          config_json TEXT NOT NULL,
          status TEXT NOT NULL,
          results_count INTEGER NOT NULL,
          started_at TEXT NOT NULL,
          completed_at TEXT,
          error TEXT
        );

        CREATE TABLE IF NOT EXISTS leadgen_results (
          id TEXT PRIMARY KEY,
          run_id TEXT NOT NULL,
          lead_id TEXT NOT NULL,
          business_name TEXT NOT NULL,
          address TEXT,
          phone TEXT,
          email TEXT,
          website TEXT,
          rating REAL,
          review_count INTEGER,
          FOREIGN KEY(run_id) REFERENCES leadgen_runs(run_id)
        );

        CREATE INDEX IF NOT EXISTS idx_leadgen_results_run ON leadgen_results(run_id);

        CREATE TABLE IF NOT EXISTS segments (
          segment_id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          source_run_id TEXT NOT NULL,
          lead_ids_json TEXT NOT NULL,
          created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS call_attempts (
          call_attempt_id TEXT PRIMARY KEY,
          campaign_id TEXT NOT NULL,
          lead_id TEXT NOT NULL,
          agent_id TEXT NOT NULL,
          call_sid TEXT,
          to_number TEXT NOT NULL,
          from_number TEXT,
          status TEXT NOT NULL,
          started_at TEXT NOT NULL,
          ended_at TEXT,
          duration_seconds INTEGER,
          recording_url TEXT,
          error TEXT,
          metadata_json TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_call_attempts_campaign ON call_attempts(campaign_id);
        CREATE INDEX IF NOT EXISTS idx_call_attempts_call_sid ON call_attempts(call_sid);

        CREATE TABLE IF NOT EXISTS call_results (
          call_result_id TEXT PRIMARY KEY,
          call_attempt_id TEXT NOT NULL,
          campaign_id TEXT NOT NULL,
          lead_id TEXT NOT NULL,
          agent_id TEXT NOT NULL,
          call_sid TEXT,
          outcome TEXT NOT NULL,
          finished_at TEXT NOT NULL,
          summary TEXT,
          metadata_json TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_call_results_attempt ON call_results(call_attempt_id);
        CREATE INDEX IF NOT EXISTS idx_call_results_call_sid ON call_results(call_sid);

        CREATE TABLE IF NOT EXISTS events (
          event_id TEXT PRIMARY KEY,
          ts TEXT NOT NULL,
          type TEXT NOT NULL,
          correlation_id TEXT NOT NULL,
          campaign_id TEXT,
          lead_id TEXT,
          agent_id TEXT,
          call_attempt_id TEXT,
          call_sid TEXT,
          run_id TEXT,
          raw_json TEXT NOT NULL,
          normalized_json TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_events_campaign ON events(campaign_id, ts);
        CREATE INDEX IF NOT EXISTS idx_events_call_sid ON events(call_sid, ts);
        """
    )








