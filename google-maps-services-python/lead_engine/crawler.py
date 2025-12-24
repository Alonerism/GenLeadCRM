"""
Website crawler for email extraction.

Crawls business websites to extract contact emails.
Max depth = 1, configurable pages per domain, no AI dependencies.
"""

import time
import logging
import re
from typing import List, Dict, Set, Optional, Tuple
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass, field
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from lead_engine.extractor import EmailExtractor, SocialLinkExtractor, extract_domain
from lead_engine.cache import LeadCache

logger = logging.getLogger(__name__)


# Priority paths to crawl
PRIORITY_PATHS = [
    '/',
    '/contact',
    '/contact-us',
    '/contactus',
    '/about',
    '/about-us',
    '/aboutus',
    '/team',
    '/our-team',
    '/staff',
    '/people',
    '/legal',
    '/privacy',
    '/privacy-policy',
    '/impressum',  # German legal page
    '/imprint',
]


@dataclass
class CrawlResult:
    """Result of crawling a website."""
    domain: str
    emails: List[Tuple[str, str]] = field(default_factory=list)  # (email, quality)
    social_links: Dict[str, str] = field(default_factory=dict)
    pages_crawled: int = 0
    success: bool = True
    error: Optional[str] = None
    
    def get_emails_list(self) -> List[str]:
        """Get just the email addresses."""
        return [email for email, _ in self.emails]
    
    def get_quality_emails(self) -> List[Tuple[str, str]]:
        """Get emails with quality flags."""
        return self.emails


class WebsiteCrawler:
    """
    Crawl websites to extract emails and social links.
    
    Features:
    - Priority path crawling (/, /contact, /about, etc.)
    - mailto: link extraction
    - Configurable limits and timeouts
    - Retry logic
    - Caching integration
    """
    
    def __init__(
        self,
        cache: LeadCache,
        max_pages: int = 6,
        timeout: int = 10,
        retries: int = 2,
        user_agent: str = "LeadEngine/1.0 (compatible; business research)",
    ):
        """
        Initialize crawler.
        
        Args:
            cache: Cache for storing results
            max_pages: Maximum pages to crawl per domain
            timeout: Request timeout in seconds
            retries: Number of retries per request
            user_agent: User-Agent header value
        """
        self.cache = cache
        self.max_pages = max_pages
        self.timeout = timeout
        self.retries = retries
        self.user_agent = user_agent
        
        # Setup session with retry logic
        self.session = self._create_session()
        
        # Extractors
        self.social_extractor = SocialLinkExtractor()
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic."""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        return session
    
    def crawl(self, website: str, use_cache: bool = True) -> CrawlResult:
        """
        Crawl a website for emails and social links.
        
        Args:
            website: Website URL
            use_cache: Whether to use cached results
            
        Returns:
            CrawlResult with extracted data
        """
        domain = extract_domain(website)
        if not domain:
            return CrawlResult(domain=website, success=False, error="Invalid URL")
        
        # Check cache
        if use_cache and self.cache.has_crawl_result(domain):
            cached = self.cache.get_crawl_result(domain)
            if cached:
                logger.debug(f"Cache hit for domain {domain}")
                return CrawlResult(
                    domain=domain,
                    emails=[(e, 'unknown') for e in cached.get('emails', [])],
                    social_links=cached.get('social_links', {}),
                    pages_crawled=cached.get('pages_crawled', 0),
                    success=cached.get('success', True),
                )
        
        # Normalize URL
        base_url = website
        if not base_url.startswith(('http://', 'https://')):
            base_url = 'https://' + base_url
        
        # Initialize result
        result = CrawlResult(domain=domain)
        
        # Track state
        crawled_urls: Set[str] = set()
        found_emails: Dict[str, str] = {}  # email -> quality
        found_social: Dict[str, str] = {}
        mailto_links: Set[str] = set()
        
        # Create email extractor for this domain
        email_extractor = EmailExtractor(domain_filter=None)  # Don't filter by domain, get all emails
        
        # Build priority URL list
        urls_to_crawl = []
        for path in PRIORITY_PATHS:
            urls_to_crawl.append(urljoin(base_url, path))
        
        # Crawl priority pages
        for url in urls_to_crawl:
            if result.pages_crawled >= self.max_pages:
                break
            
            if url in crawled_urls:
                continue
            
            try:
                content, discovered_urls, page_mailto = self._fetch_page(url)
                crawled_urls.add(url)
                result.pages_crawled += 1
                
                if content:
                    # Extract emails
                    for email, quality in email_extractor.extract_with_quality(content):
                        if email not in found_emails:
                            found_emails[email] = quality
                    
                    # Extract social links
                    social = self.social_extractor.extract(content)
                    found_social.update(social)
                    
                    # Collect mailto links
                    mailto_links.update(page_mailto)
                
                # Small delay between requests
                time.sleep(0.2)
                
            except Exception as e:
                logger.debug(f"Error crawling {url}: {e}")
                continue
        
        # Process mailto links (highest confidence emails)
        for email in mailto_links:
            email = email.lower().strip()
            if email and '@' in email:
                quality = email_extractor._classify_quality(email)
                if email not in found_emails:
                    found_emails[email] = quality
        
        # Build final result
        result.emails = [(email, quality) for email, quality in found_emails.items()]
        result.social_links = found_social
        result.success = True
        
        # Save to cache
        self.cache.save_crawl_result(
            domain=domain,
            emails=[e for e, _ in result.emails],
            social_links=result.social_links,
            pages_crawled=result.pages_crawled,
            raw_data={'urls_crawled': list(crawled_urls)},
            success=True,
        )
        
        logger.debug(f"Crawled {domain}: {len(result.emails)} emails, {result.pages_crawled} pages")
        
        return result
    
    def _fetch_page(self, url: str) -> Tuple[Optional[str], List[str], Set[str]]:
        """
        Fetch a single page.
        
        Args:
            url: URL to fetch
            
        Returns:
            Tuple of (content, discovered_urls, mailto_links)
        """
        discovered_urls = []
        mailto_links: Set[str] = set()
        
        try:
            response = self.session.get(
                url,
                timeout=self.timeout,
                allow_redirects=True,
            )
            
            # Check content type
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type.lower() and 'application/xhtml' not in content_type.lower():
                return None, discovered_urls, mailto_links
            
            response.raise_for_status()
            content = response.text
            
            # Extract mailto links
            mailto_pattern = re.compile(r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', re.I)
            for match in mailto_pattern.finditer(content):
                mailto_links.add(match.group(1))
            
            # Extract links for discovery (depth 1)
            link_pattern = re.compile(r'href=["\']([^"\']+)["\']', re.I)
            base_domain = extract_domain(url)
            
            for match in link_pattern.finditer(content):
                link = match.group(1)
                if link.startswith('mailto:'):
                    continue
                
                # Make absolute
                abs_link = urljoin(url, link)
                link_domain = extract_domain(abs_link)
                
                # Only follow same-domain links
                if link_domain == base_domain:
                    discovered_urls.append(abs_link)
            
            return content, discovered_urls, mailto_links
            
        except requests.exceptions.Timeout:
            logger.debug(f"Timeout fetching {url}")
            self.cache.save_failure('crawl_timeout', f"Timeout: {url}", domain=extract_domain(url))
            return None, discovered_urls, mailto_links
        except requests.exceptions.RequestException as e:
            logger.debug(f"Request error for {url}: {e}")
            return None, discovered_urls, mailto_links
        except Exception as e:
            logger.debug(f"Error fetching {url}: {e}")
            return None, discovered_urls, mailto_links
    
    def crawl_batch(self, websites: List[str], use_cache: bool = True) -> Dict[str, CrawlResult]:
        """
        Crawl multiple websites.
        
        Args:
            websites: List of website URLs
            use_cache: Whether to use cached results
            
        Returns:
            Dict mapping domain to CrawlResult
        """
        results = {}
        
        for website in websites:
            if not website:
                continue
            
            domain = extract_domain(website)
            if not domain or domain in results:
                continue
            
            result = self.crawl(website, use_cache=use_cache)
            results[domain] = result
            
            # Small delay between domains
            time.sleep(0.1)
        
        return results

