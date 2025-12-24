"""
SQLite caching layer for Lead Engine.

Caches place details and crawl results to minimize API calls and enable resume.
"""

import sqlite3
import json
import zlib
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class LeadCache:
    """SQLite-based cache for places data and crawl results."""
    
    SCHEMA = """
    CREATE TABLE IF NOT EXISTS places (
        place_id TEXT PRIMARY KEY,
        name TEXT,
        address TEXT,
        phone TEXT,
        international_phone TEXT,
        website TEXT,
        types TEXT,
        rating REAL,
        user_ratings_total INTEGER,
        raw_response BLOB,
        source_query TEXT,
        source_location TEXT,
        fetched_at TEXT,
        updated_at TEXT
    );
    
    CREATE TABLE IF NOT EXISTS crawl_results (
        domain TEXT PRIMARY KEY,
        emails TEXT,
        social_links TEXT,
        pages_crawled INTEGER,
        raw_data BLOB,
        crawled_at TEXT,
        success INTEGER
    );
    
    CREATE TABLE IF NOT EXISTS search_progress (
        query_hash TEXT PRIMARY KEY,
        query TEXT,
        location TEXT,
        next_page_token TEXT,
        results_fetched INTEGER,
        completed INTEGER,
        updated_at TEXT
    );
    
    CREATE TABLE IF NOT EXISTS failures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        place_id TEXT,
        domain TEXT,
        error_type TEXT,
        error_message TEXT,
        retry_count INTEGER DEFAULT 0,
        created_at TEXT
    );
    
    CREATE INDEX IF NOT EXISTS idx_places_website ON places(website);
    CREATE INDEX IF NOT EXISTS idx_places_phone ON places(phone);
    CREATE INDEX IF NOT EXISTS idx_failures_domain ON failures(domain);
    """
    
    def __init__(self, db_path: str = "lead_cache.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the database schema."""
        with self._get_conn() as conn:
            conn.executescript(self.SCHEMA)
            conn.commit()
    
    @contextmanager
    def _get_conn(self):
        """Get a database connection with context management."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _compress(self, data: Any) -> bytes:
        """Compress JSON data."""
        return zlib.compress(json.dumps(data).encode('utf-8'))
    
    def _decompress(self, data: bytes) -> Any:
        """Decompress JSON data."""
        if data is None:
            return None
        return json.loads(zlib.decompress(data).decode('utf-8'))
    
    def _query_hash(self, query: str, location: str) -> str:
        """Generate hash for query+location pair."""
        return hashlib.md5(f"{query}|{location}".lower().encode()).hexdigest()
    
    # Place methods
    def get_place(self, place_id: str) -> Optional[Dict[str, Any]]:
        """Get cached place details."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM places WHERE place_id = ?", (place_id,)
            ).fetchone()
            if row:
                result = dict(row)
                result['raw_response'] = self._decompress(result['raw_response'])
                result['types'] = json.loads(result['types']) if result['types'] else []
                return result
            return None
    
    def has_place(self, place_id: str) -> bool:
        """Check if place exists in cache."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM places WHERE place_id = ?", (place_id,)
            ).fetchone()
            return row is not None
    
    def save_place(self, place_data: Dict[str, Any], source_query: str = "", source_location: str = ""):
        """Save place details to cache."""
        now = datetime.utcnow().isoformat()
        
        # Extract fields
        place_id = place_data.get('place_id', '')
        result = place_data.get('result', place_data)
        
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO places 
                (place_id, name, address, phone, international_phone, website, 
                 types, rating, user_ratings_total, raw_response, 
                 source_query, source_location, fetched_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                place_id,
                result.get('name', ''),
                result.get('formatted_address', ''),
                result.get('formatted_phone_number', ''),
                result.get('international_phone_number', ''),
                result.get('website', ''),
                json.dumps(result.get('types', [])),
                result.get('rating'),
                result.get('user_ratings_total'),
                self._compress(place_data),
                source_query,
                source_location,
                now,
                now,
            ))
            conn.commit()
    
    def get_all_places(self) -> List[Dict[str, Any]]:
        """Get all cached places."""
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM places ORDER BY fetched_at DESC").fetchall()
            results = []
            for row in rows:
                result = dict(row)
                result['raw_response'] = self._decompress(result['raw_response'])
                result['types'] = json.loads(result['types']) if result['types'] else []
                results.append(result)
            return results
    
    def get_places_by_query(self, query: str, location: str) -> List[Dict[str, Any]]:
        """Get places for a specific query/location."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM places WHERE source_query = ? AND source_location = ?",
                (query, location)
            ).fetchall()
            results = []
            for row in rows:
                result = dict(row)
                result['raw_response'] = self._decompress(result['raw_response'])
                result['types'] = json.loads(result['types']) if result['types'] else []
                results.append(result)
            return results
    
    # Crawl results methods
    def get_crawl_result(self, domain: str) -> Optional[Dict[str, Any]]:
        """Get cached crawl result for domain."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM crawl_results WHERE domain = ?", (domain,)
            ).fetchone()
            if row:
                result = dict(row)
                result['emails'] = json.loads(result['emails']) if result['emails'] else []
                result['social_links'] = json.loads(result['social_links']) if result['social_links'] else {}
                result['raw_data'] = self._decompress(result['raw_data'])
                return result
            return None
    
    def has_crawl_result(self, domain: str) -> bool:
        """Check if crawl result exists for domain."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM crawl_results WHERE domain = ?", (domain,)
            ).fetchone()
            return row is not None
    
    def save_crawl_result(self, domain: str, emails: List[str], social_links: Dict[str, str],
                          pages_crawled: int, raw_data: Any = None, success: bool = True):
        """Save crawl result to cache."""
        now = datetime.utcnow().isoformat()
        
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO crawl_results
                (domain, emails, social_links, pages_crawled, raw_data, crawled_at, success)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                domain,
                json.dumps(emails),
                json.dumps(social_links),
                pages_crawled,
                self._compress(raw_data) if raw_data else None,
                now,
                1 if success else 0,
            ))
            conn.commit()
    
    # Search progress methods
    def get_search_progress(self, query: str, location: str) -> Optional[Dict[str, Any]]:
        """Get search progress for resume capability."""
        query_hash = self._query_hash(query, location)
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM search_progress WHERE query_hash = ?", (query_hash,)
            ).fetchone()
            return dict(row) if row else None
    
    def save_search_progress(self, query: str, location: str, next_page_token: Optional[str],
                              results_fetched: int, completed: bool = False):
        """Save search progress for resume capability."""
        query_hash = self._query_hash(query, location)
        now = datetime.utcnow().isoformat()
        
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO search_progress
                (query_hash, query, location, next_page_token, results_fetched, completed, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                query_hash,
                query,
                location,
                next_page_token,
                results_fetched,
                1 if completed else 0,
                now,
            ))
            conn.commit()
    
    # Failure tracking methods
    def save_failure(self, error_type: str, error_message: str,
                     place_id: str = None, domain: str = None):
        """Save a failure for later retry."""
        now = datetime.utcnow().isoformat()
        
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO failures (place_id, domain, error_type, error_message, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (place_id, domain, error_type, error_message, now))
            conn.commit()
    
    def get_failures(self, error_type: str = None) -> List[Dict[str, Any]]:
        """Get failures, optionally filtered by type."""
        with self._get_conn() as conn:
            if error_type:
                rows = conn.execute(
                    "SELECT * FROM failures WHERE error_type = ? ORDER BY created_at DESC",
                    (error_type,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM failures ORDER BY created_at DESC"
                ).fetchall()
            return [dict(row) for row in rows]
    
    def clear_failures(self, error_type: str = None):
        """Clear failures, optionally filtered by type."""
        with self._get_conn() as conn:
            if error_type:
                conn.execute("DELETE FROM failures WHERE error_type = ?", (error_type,))
            else:
                conn.execute("DELETE FROM failures")
            conn.commit()
    
    # Utility methods
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        with self._get_conn() as conn:
            places_count = conn.execute("SELECT COUNT(*) FROM places").fetchone()[0]
            crawl_count = conn.execute("SELECT COUNT(*) FROM crawl_results").fetchone()[0]
            failures_count = conn.execute("SELECT COUNT(*) FROM failures").fetchone()[0]
            
            return {
                "places_cached": places_count,
                "domains_crawled": crawl_count,
                "failures": failures_count,
            }
    
    def get_unique_domains(self) -> List[str]:
        """Get list of unique website domains from places."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT DISTINCT website FROM places WHERE website IS NOT NULL AND website != ''"
            ).fetchall()
            return [row[0] for row in rows]
    
    def update_place_emails(self, place_id: str, emails: List[str]):
        """Update emails for a place (stored via crawl results)."""
        # Emails are stored in crawl_results by domain, not in places
        # This is intentional to avoid duplicate data
        pass

