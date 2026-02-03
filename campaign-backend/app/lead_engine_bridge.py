from __future__ import annotations

import os
import sys
from typing import Any


def _ensure_lead_engine_importable() -> None:
    # This repo includes the lead engine under google-maps-services-python/.
    # We add it to sys.path so we can import without rewriting that project.
    here = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    repo_root = os.path.abspath(os.path.join(here, ".."))
    lead_engine_root = os.path.join(repo_root, "google-maps-services-python")
    if lead_engine_root not in sys.path:
        sys.path.insert(0, lead_engine_root)


def run_lead_engine(config: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Runs the existing lead engine pipeline and returns JSON-ish dicts.
    """
    _ensure_lead_engine_importable()

    from lead_engine.config import Config  # type: ignore
    from lead_engine.cache import LeadCache  # type: ignore
    from lead_engine.output import ProgressTracker  # type: ignore
    from lead_engine.__main__ import run_pipeline  # type: ignore

    # Map UI config to lead-engine config (some fields are stored but not used).
    query = config["query"]
    location = config["location"]
    max_results = int(config.get("max_results") or 100)
    max_pages = int(config.get("max_pages") or 3)
    no_crawl = bool(config.get("no_crawl") or False)

    # Lead engine supports max_pages 1-3.
    max_pages = max(1, min(3, max_pages))

    cfg = Config(
        google_api_key=os.environ.get("GOOGLE_MAPS_API_KEY", ""),
        query=query,
        location=location,
        max_results=max_results,
        max_pages=max_pages,
        crawl_enabled=(not no_crawl),
        # Ensure cache stays in the lead-engine folder by default.
        cache_db=os.environ.get("LEAD_ENGINE_CACHE_DB", "lead_cache.db"),
        use_cache=True,
        resume=False,
        output_dir=os.environ.get("LEAD_ENGINE_OUTPUT_DIR", "output"),
    )
    errors = cfg.validate()
    if errors:
        raise RuntimeError("; ".join(errors))

    cache = LeadCache(cfg.cache_db)
    progress = ProgressTracker(quiet=True)

    leads = run_pipeline([(query, location)], cfg, cache, progress)

    out: list[dict[str, Any]] = []
    for l in leads:
        d = l.to_full_dict()
        # Normalize email list; lead engine returns emails list in JSONL dict.
        emails = d.get("emails") or []
        if isinstance(emails, str):
            emails = [e.strip() for e in emails.split(";") if e.strip()]
        out.append(
            {
                "place_id": d.get("place_id"),
                "name": d.get("name") or "",
                "address": d.get("address") or "",
                "phone": d.get("phone") or None,
                "email": (emails[0] if emails else None),
                "emails": emails,
                "website": d.get("website") or None,
                "rating": d.get("rating"),
                "review_count": d.get("user_ratings_total"),
                "source_query": d.get("source_query"),
                "source_location": d.get("source_location"),
                "raw": d,
            }
        )
    return out








