"""
Lead deduplication logic.

Deduplicates leads by:
- Primary key: place_id
- Secondary: normalized phone OR normalized website domain
"""

import re
import logging
from typing import List, Dict, Any, Set, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

from lead_engine.extractor import extract_domain, PhoneNormalizer

logger = logging.getLogger(__name__)


@dataclass
class Lead:
    """Represents a deduplicated business lead."""
    place_id: str
    name: str
    address: str
    city: str = ""
    state: str = ""
    postal_code: str = ""
    country: str = ""
    phone: str = ""
    international_phone: str = ""
    website: str = ""
    domain: str = ""
    emails: List[str] = None
    email_quality: Dict[str, str] = None  # email -> quality
    types: List[str] = None
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None
    source_query: str = ""
    source_location: str = ""
    fetched_at: str = ""
    
    def __post_init__(self):
        if self.emails is None:
            self.emails = []
        if self.email_quality is None:
            self.email_quality = {}
        if self.types is None:
            self.types = []
        
        # Parse address if not already parsed
        if self.address and not self.city:
            self._parse_address()
        
        # Extract domain from website
        if self.website and not self.domain:
            self.domain = extract_domain(self.website) or ""
    
    def _parse_address(self):
        """Parse address into components (US-focused)."""
        if not self.address:
            return
        
        parts = self.address.split(',')
        
        if len(parts) >= 3:
            # Typical format: "Street, City, State ZIP, Country"
            self.city = parts[-3].strip() if len(parts) >= 3 else ""
            
            state_zip = parts[-2].strip() if len(parts) >= 2 else ""
            # Parse state and zip
            match = re.match(r'([A-Za-z]{2})\s+(\d{5}(?:-\d{4})?)', state_zip)
            if match:
                self.state = match.group(1).upper()
                self.postal_code = match.group(2)
            else:
                self.state = state_zip
            
            self.country = parts[-1].strip() if len(parts) >= 1 else ""
        elif len(parts) == 2:
            self.city = parts[0].strip()
            self.country = parts[1].strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for output."""
        return {
            'place_id': self.place_id,
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'country': self.country,
            'phone': self.phone,
            'international_phone': self.international_phone,
            'website': self.website,
            'emails': ';'.join(self.emails),
            'types': ';'.join(self.types),
            'rating': self.rating,
            'user_ratings_total': self.user_ratings_total,
            'source_query': self.source_query,
            'source_location': self.source_location,
            'fetched_at': self.fetched_at,
        }
    
    def to_full_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with all fields for JSONL."""
        result = self.to_dict()
        result['emails'] = self.emails  # Keep as list
        result['types'] = self.types  # Keep as list
        result['domain'] = self.domain
        result['email_quality'] = self.email_quality
        return result


class LeadDeduplicator:
    """Deduplicates leads across multiple sources."""
    
    def __init__(self):
        self.phone_normalizer = PhoneNormalizer()
        
        # Tracking indexes
        self._place_ids: Set[str] = set()
        self._phone_to_place: Dict[str, str] = {}  # normalized_phone -> place_id
        self._domain_to_place: Dict[str, str] = {}  # domain -> place_id
        
        # Stats
        self._total_input = 0
        self._duplicates_place_id = 0
        self._duplicates_phone = 0
        self._duplicates_domain = 0
    
    def dedupe(self, leads: List[Dict[str, Any]]) -> List[Lead]:
        """
        Deduplicate a list of leads.
        
        Args:
            leads: List of lead dictionaries
            
        Returns:
            List of deduplicated Lead objects
        """
        result = []
        
        for lead_data in leads:
            self._total_input += 1
            
            place_id = lead_data.get('place_id', '')
            phone = lead_data.get('phone', '')
            website = lead_data.get('website', '')
            
            # Normalize identifiers
            norm_phone = self.phone_normalizer.normalize(phone) if phone else ''
            domain = extract_domain(website) if website else ''
            
            # Check for duplicates
            is_dup, dup_reason, existing_id = self._check_duplicate(place_id, norm_phone, domain)
            
            if is_dup:
                logger.debug(f"Duplicate lead: {lead_data.get('name', '')} ({dup_reason})")
                if dup_reason == 'place_id':
                    self._duplicates_place_id += 1
                elif dup_reason == 'phone':
                    self._duplicates_phone += 1
                elif dup_reason == 'domain':
                    self._duplicates_domain += 1
                continue
            
            # Create Lead object
            lead = self._create_lead(lead_data)
            
            # Register identifiers
            self._place_ids.add(place_id)
            if norm_phone:
                self._phone_to_place[norm_phone] = place_id
            if domain:
                self._domain_to_place[domain] = place_id
            
            result.append(lead)
        
        return result
    
    def _check_duplicate(self, place_id: str, norm_phone: str, domain: str) -> Tuple[bool, str, Optional[str]]:
        """
        Check if lead is duplicate.
        
        Returns:
            Tuple of (is_duplicate, reason, existing_place_id)
        """
        # Primary: place_id
        if place_id in self._place_ids:
            return True, 'place_id', place_id
        
        # Secondary: phone
        if norm_phone and norm_phone in self._phone_to_place:
            return True, 'phone', self._phone_to_place[norm_phone]
        
        # Secondary: domain
        if domain and domain in self._domain_to_place:
            return True, 'domain', self._domain_to_place[domain]
        
        return False, '', None
    
    def _create_lead(self, data: Dict[str, Any]) -> Lead:
        """Create Lead object from dictionary."""
        return Lead(
            place_id=data.get('place_id', ''),
            name=data.get('name', ''),
            address=data.get('address', ''),
            phone=data.get('phone', ''),
            international_phone=data.get('international_phone', ''),
            website=data.get('website', ''),
            emails=data.get('emails', []),
            email_quality=data.get('email_quality', {}),
            types=data.get('types', []),
            rating=data.get('rating'),
            user_ratings_total=data.get('user_ratings_total'),
            source_query=data.get('source_query', ''),
            source_location=data.get('source_location', ''),
            fetched_at=data.get('fetched_at', ''),
        )
    
    def add_emails_to_lead(self, lead: Lead, emails: List[str], email_quality: Dict[str, str] = None):
        """Add emails to an existing lead."""
        for email in emails:
            if email not in lead.emails:
                lead.emails.append(email)
                if email_quality and email in email_quality:
                    lead.email_quality[email] = email_quality[email]
    
    def get_stats(self) -> Dict[str, int]:
        """Get deduplication statistics."""
        return {
            'total_input': self._total_input,
            'unique_leads': len(self._place_ids),
            'duplicates_place_id': self._duplicates_place_id,
            'duplicates_phone': self._duplicates_phone,
            'duplicates_domain': self._duplicates_domain,
            'total_duplicates': self._duplicates_place_id + self._duplicates_phone + self._duplicates_domain,
        }
    
    def reset(self):
        """Reset deduplication state."""
        self._place_ids.clear()
        self._phone_to_place.clear()
        self._domain_to_place.clear()
        self._total_input = 0
        self._duplicates_place_id = 0
        self._duplicates_phone = 0
        self._duplicates_domain = 0


def merge_leads_with_emails(
    leads: List[Lead],
    crawl_results: Dict[str, Any],
) -> List[Lead]:
    """
    Merge crawl results (emails) into leads.
    
    Args:
        leads: List of Lead objects
        crawl_results: Dict mapping domain to CrawlResult
        
    Returns:
        Leads with emails populated
    """
    for lead in leads:
        domain = lead.domain or extract_domain(lead.website)
        if not domain:
            continue
        
        crawl_result = crawl_results.get(domain)
        if not crawl_result:
            continue
        
        # Add emails
        for email, quality in crawl_result.emails:
            if email not in lead.emails:
                lead.emails.append(email)
                lead.email_quality[email] = quality
    
    return leads

