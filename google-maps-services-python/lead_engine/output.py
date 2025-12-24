"""
Output writers for leads.

Supports CSV and JSONL output formats.
"""

import csv
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from lead_engine.dedupe import Lead

logger = logging.getLogger(__name__)


# CSV column order
CSV_COLUMNS = [
    'place_id',
    'name',
    'address',
    'city',
    'state',
    'postal_code',
    'country',
    'phone',
    'international_phone',
    'website',
    'emails',
    'types',
    'rating',
    'user_ratings_total',
    'source_query',
    'source_location',
    'fetched_at',
]


class OutputWriter:
    """Writes leads to CSV and JSONL files."""
    
    def __init__(self, output_dir: str = "output", prefix: str = "leads"):
        """
        Initialize output writer.
        
        Args:
            output_dir: Output directory path
            prefix: File name prefix
        """
        self.output_dir = Path(output_dir)
        self.prefix = prefix
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamp for unique files
        self._timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    @property
    def csv_path(self) -> Path:
        """Get CSV output path."""
        return self.output_dir / f"{self.prefix}.csv"
    
    @property
    def jsonl_path(self) -> Path:
        """Get JSONL output path."""
        return self.output_dir / f"{self.prefix}.jsonl"
    
    @property
    def failures_path(self) -> Path:
        """Get failures CSV path."""
        return self.output_dir / f"{self.prefix}_failures.csv"
    
    def write_leads(self, leads: List[Lead], append: bool = False):
        """
        Write leads to both CSV and JSONL.
        
        Args:
            leads: List of Lead objects
            append: Whether to append to existing files
        """
        self.write_csv(leads, append=append)
        self.write_jsonl(leads, append=append)
        
        logger.info(f"Wrote {len(leads)} leads to {self.csv_path} and {self.jsonl_path}")
    
    def write_csv(self, leads: List[Lead], append: bool = False):
        """
        Write leads to CSV file.
        
        Args:
            leads: List of Lead objects
            append: Whether to append to existing file
        """
        mode = 'a' if append else 'w'
        write_header = not append or not self.csv_path.exists()
        
        with open(self.csv_path, mode, newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction='ignore')
            
            if write_header:
                writer.writeheader()
            
            for lead in leads:
                row = lead.to_dict()
                writer.writerow(row)
    
    def write_jsonl(self, leads: List[Lead], append: bool = False):
        """
        Write leads to JSONL file.
        
        Args:
            leads: List of Lead objects
            append: Whether to append to existing file
        """
        mode = 'a' if append else 'w'
        
        with open(self.jsonl_path, mode, encoding='utf-8') as f:
            for lead in leads:
                data = lead.to_full_dict()
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
    
    def write_failures(self, failures: List[Dict[str, Any]]):
        """
        Write failures to CSV file.
        
        Args:
            failures: List of failure records
        """
        if not failures:
            return
        
        fieldnames = ['place_id', 'domain', 'error_type', 'error_message', 'retry_count', 'created_at']
        
        with open(self.failures_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(failures)
        
        logger.info(f"Wrote {len(failures)} failures to {self.failures_path}")
    
    def read_existing_place_ids(self) -> set:
        """
        Read existing place_ids from CSV for resume capability.
        
        Returns:
            Set of existing place_ids
        """
        place_ids = set()
        
        if not self.csv_path.exists():
            return place_ids
        
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('place_id'):
                        place_ids.add(row['place_id'])
        except Exception as e:
            logger.warning(f"Error reading existing CSV: {e}")
        
        return place_ids


class ProgressTracker:
    """Track and display progress during lead generation."""
    
    def __init__(self, total: Optional[int] = None, quiet: bool = False):
        """
        Initialize progress tracker.
        
        Args:
            total: Total expected items (for percentage)
            quiet: Whether to suppress output
        """
        self.total = total
        self.quiet = quiet
        self.current = 0
        self.start_time = datetime.now()
        
        # Stats
        self.places_fetched = 0
        self.websites_crawled = 0
        self.emails_found = 0
        self.api_calls = 0
        self.cache_hits = 0
    
    def update(self, places: int = 0, websites: int = 0, emails: int = 0, 
               api_calls: int = 0, cache_hits: int = 0):
        """Update progress counters."""
        self.places_fetched += places
        self.websites_crawled += websites
        self.emails_found += emails
        self.api_calls += api_calls
        self.cache_hits += cache_hits
        self.current = self.places_fetched
        
        if not self.quiet:
            self._print_progress()
    
    def _print_progress(self):
        """Print current progress."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        parts = [
            f"Places: {self.places_fetched}",
            f"Websites: {self.websites_crawled}",
            f"Emails: {self.emails_found}",
        ]
        
        if self.total:
            pct = (self.current / self.total) * 100
            parts.insert(0, f"{pct:.1f}%")
        
        if elapsed > 0:
            rate = self.places_fetched / elapsed
            parts.append(f"({rate:.1f}/s)")
        
        print(f"\r{' | '.join(parts)}", end='', flush=True)
    
    def finish(self):
        """Print final summary."""
        if self.quiet:
            return
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        print()  # New line after progress
        print(f"\n{'='*50}")
        print(f"Lead Generation Complete")
        print(f"{'='*50}")
        print(f"  Places fetched:     {self.places_fetched}")
        print(f"  Websites crawled:   {self.websites_crawled}")
        print(f"  Emails found:       {self.emails_found}")
        print(f"  API calls:          {self.api_calls}")
        print(f"  Cache hits:         {self.cache_hits}")
        print(f"  Time elapsed:       {elapsed:.1f}s")
        print(f"{'='*50}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get progress statistics."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return {
            'places_fetched': self.places_fetched,
            'websites_crawled': self.websites_crawled,
            'emails_found': self.emails_found,
            'api_calls': self.api_calls,
            'cache_hits': self.cache_hits,
            'elapsed_seconds': elapsed,
        }

