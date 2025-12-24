"""
Email and phone extraction utilities.

Robust regex-based extraction with normalization and quality flags.
No AI/LLM dependencies.
"""

import re
from typing import List, Set, Tuple, Optional, Dict
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class EmailExtractor:
    """Extract and validate emails from text and HTML content."""
    
    # Comprehensive email regex
    EMAIL_PATTERN = re.compile(
        r'''(?x)
        (?<![a-zA-Z0-9._%+-])  # Not preceded by email chars
        [a-zA-Z0-9._%+-]{1,64}  # Local part (max 64 chars)
        @
        [a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?  # Domain part
        (?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+  # Subdomains/TLD
        (?![a-zA-Z0-9._%+-])  # Not followed by email chars
        ''',
        re.IGNORECASE
    )
    
    # Mailto link pattern
    MAILTO_PATTERN = re.compile(
        r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        re.IGNORECASE
    )
    
    # Common generic email prefixes (likely not personal contacts)
    GENERIC_PREFIXES = {
        'info', 'contact', 'hello', 'hi', 'support', 'help', 'admin',
        'sales', 'marketing', 'billing', 'accounts', 'service', 'services',
        'team', 'office', 'mail', 'email', 'enquiry', 'enquiries',
        'inquiry', 'inquiries', 'general', 'feedback', 'webmaster',
        'postmaster', 'hostmaster', 'abuse', 'noreply', 'no-reply',
        'donotreply', 'do-not-reply', 'newsletter', 'subscribe',
        'unsubscribe', 'privacy', 'legal', 'compliance', 'hr',
        'jobs', 'careers', 'recruitment', 'press', 'media', 'pr',
    }
    
    # Invalid TLDs and patterns to filter
    INVALID_TLDS = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'css', 'js', 'json', 'xml'}
    INVALID_DOMAINS = {'example.com', 'example.org', 'test.com', 'domain.com', 'email.com',
                       'yoursite.com', 'yourdomain.com', 'company.com', 'website.com',
                       'sentry.io', 'wixpress.com', 'googleapis.com'}
    
    def __init__(self, domain_filter: Optional[str] = None):
        """
        Initialize extractor.
        
        Args:
            domain_filter: If set, only extract emails from this domain
        """
        self.domain_filter = domain_filter.lower() if domain_filter else None
    
    def extract(self, text: str) -> List[str]:
        """
        Extract all valid emails from text.
        
        Args:
            text: Raw text or HTML content
            
        Returns:
            List of unique, normalized email addresses
        """
        emails: Set[str] = set()
        
        # Extract from mailto links first (higher confidence)
        for match in self.MAILTO_PATTERN.finditer(text):
            email = self._normalize(match.group(1))
            if email and self._is_valid(email):
                emails.add(email)
        
        # Extract from general text
        for match in self.EMAIL_PATTERN.finditer(text):
            email = self._normalize(match.group(0))
            if email and self._is_valid(email):
                emails.add(email)
        
        return sorted(emails)
    
    def extract_with_quality(self, text: str) -> List[Tuple[str, str]]:
        """
        Extract emails with quality classification.
        
        Args:
            text: Raw text or HTML content
            
        Returns:
            List of (email, quality) tuples where quality is 'personal' or 'generic'
        """
        emails = self.extract(text)
        return [(email, self._classify_quality(email)) for email in emails]
    
    def _normalize(self, email: str) -> Optional[str]:
        """Normalize email address."""
        if not email:
            return None
        
        email = email.lower().strip()
        
        # Remove common URL artifacts
        email = email.rstrip('.')
        email = email.rstrip(',')
        email = email.rstrip(';')
        email = email.rstrip(')')
        email = email.rstrip(']')
        email = email.rstrip('>')
        
        # Remove leading artifacts
        email = email.lstrip('(')
        email = email.lstrip('[')
        email = email.lstrip('<')
        
        return email if '@' in email else None
    
    def _is_valid(self, email: str) -> bool:
        """Validate email address."""
        if not email or '@' not in email:
            return False
        
        local, domain = email.rsplit('@', 1)
        
        # Check local part
        if not local or len(local) > 64:
            return False
        
        # Check domain
        if not domain or '.' not in domain:
            return False
        
        # Check TLD
        tld = domain.split('.')[-1]
        if tld in self.INVALID_TLDS:
            return False
        if len(tld) < 2 or len(tld) > 10:
            return False
        
        # Check against invalid domains
        if domain in self.INVALID_DOMAINS:
            return False
        
        # Domain filter
        if self.domain_filter:
            if not domain.endswith(self.domain_filter):
                return False
        
        # Check for obvious placeholders
        placeholder_patterns = [
            r'your.*email', r'email.*here', r'name@', r'@domain',
            r'xxx', r'test@', r'@test', r'sample@', r'@sample'
        ]
        for pattern in placeholder_patterns:
            if re.search(pattern, email, re.IGNORECASE):
                return False
        
        return True
    
    def _classify_quality(self, email: str) -> str:
        """Classify email as 'personal' or 'generic'."""
        if not email or '@' not in email:
            return 'generic'
        
        local = email.split('@')[0].lower()
        
        # Check against generic prefixes
        # Handle common patterns like info1, contact2, etc.
        base_local = re.sub(r'\d+$', '', local)
        
        if base_local in self.GENERIC_PREFIXES:
            return 'generic'
        
        # Check for role-based patterns
        role_patterns = ['sales', 'support', 'info', 'admin', 'contact']
        for pattern in role_patterns:
            if local.startswith(pattern) or local.endswith(pattern):
                return 'generic'
        
        return 'personal'


class PhoneNormalizer:
    """Normalize and validate phone numbers."""
    
    # Pattern to extract phone-like strings
    PHONE_PATTERN = re.compile(
        r'''(?x)
        (?:
            (?:\+?1[-.\s]?)?  # Optional US/Canada country code
            (?:\(?\d{3}\)?[-.\s]?)  # Area code
            \d{3}[-.\s]?\d{4}  # Main number
        )
        |
        (?:
            \+\d{1,3}[-.\s]?  # International country code
            (?:\(?\d{1,4}\)?[-.\s]?)?  # Optional area code
            \d{4,14}  # Main number (flexible)
        )
        ''',
        re.VERBOSE
    )
    
    def __init__(self):
        pass
    
    def normalize(self, phone: str) -> str:
        """
        Normalize phone number to consistent format.
        
        Args:
            phone: Raw phone number string
            
        Returns:
            Normalized phone number (digits only with optional + prefix)
        """
        if not phone:
            return ""
        
        # Keep only digits and + sign
        normalized = re.sub(r'[^\d+]', '', phone)
        
        # Ensure + is only at the start
        if '+' in normalized:
            parts = normalized.split('+')
            # Take the part after the last + if there are multiple
            normalized = '+' + ''.join(parts).lstrip('+')
        
        return normalized
    
    def extract(self, text: str) -> List[str]:
        """Extract phone numbers from text."""
        phones = []
        for match in self.PHONE_PATTERN.finditer(text):
            normalized = self.normalize(match.group(0))
            if self._is_valid(normalized):
                phones.append(normalized)
        return list(set(phones))
    
    def _is_valid(self, phone: str) -> bool:
        """Validate phone number."""
        if not phone:
            return False
        
        # Remove + for length check
        digits = phone.lstrip('+')
        
        # Valid phone numbers have 7-15 digits
        if len(digits) < 7 or len(digits) > 15:
            return False
        
        # Check for obvious invalid patterns (all same digit, sequential)
        if len(set(digits)) == 1:
            return False
        
        return True
    
    def format_display(self, phone: str) -> str:
        """Format phone for display (US format if applicable)."""
        normalized = self.normalize(phone)
        digits = normalized.lstrip('+')
        
        # US/Canada format
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits.startswith('1'):
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        
        # International - just add spaces
        if normalized.startswith('+'):
            return normalized
        
        return phone  # Return original if can't format


class SocialLinkExtractor:
    """Extract social media links from HTML content."""
    
    SOCIAL_PATTERNS = {
        'linkedin': re.compile(r'https?://(?:www\.)?linkedin\.com/(?:company|in)/[a-zA-Z0-9_-]+/?', re.I),
        'facebook': re.compile(r'https?://(?:www\.)?facebook\.com/[a-zA-Z0-9._-]+/?', re.I),
        'instagram': re.compile(r'https?://(?:www\.)?instagram\.com/[a-zA-Z0-9._-]+/?', re.I),
        'twitter': re.compile(r'https?://(?:www\.)?(?:twitter|x)\.com/[a-zA-Z0-9_]+/?', re.I),
        'youtube': re.compile(r'https?://(?:www\.)?youtube\.com/(?:c/|channel/|user/)?[a-zA-Z0-9_-]+/?', re.I),
    }
    
    def extract(self, text: str) -> Dict[str, str]:
        """
        Extract social media links from text.
        
        Args:
            text: HTML or text content
            
        Returns:
            Dict mapping platform name to URL
        """
        results = {}
        
        for platform, pattern in self.SOCIAL_PATTERNS.items():
            match = pattern.search(text)
            if match:
                url = match.group(0).rstrip('/')
                # Validate it's not a share/intent link
                if '/sharer' not in url and '/intent' not in url and '/share' not in url:
                    results[platform] = url
        
        return results


def extract_domain(url: str) -> Optional[str]:
    """Extract domain from URL."""
    if not url:
        return None
    
    try:
        # Add scheme if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Remove port
        if ':' in domain:
            domain = domain.split(':')[0]
        
        return domain if domain else None
    except Exception:
        return None

