"""
Google Places API acquisition module.

Handles searching for places and fetching details with minimal API calls.
"""

import time
import logging
from typing import List, Dict, Any, Optional, Generator, Tuple
from dataclasses import dataclass

import googlemaps
from googlemaps.exceptions import ApiError, Timeout, TransportError

from lead_engine.cache import LeadCache
from lead_engine.config import Config

logger = logging.getLogger(__name__)


# Minimal fields for cost optimization
SEARCH_FIELDS = [
    'place_id',
    'name',
    'formatted_address',
    'types',
]

# Place Details field mask (minimized for correctness + low API cost).
# NOTE: The underlying `googlemaps` client validates fields against its
# `PLACES_DETAIL_FIELDS` set; it supports `type` (singular) but not `types`.
# We only request what we need for the minimal working pipeline.
DETAIL_FIELDS = [
    'place_id',
    'name',
    'formatted_phone_number',
    'international_phone_number',
    'website',
]


@dataclass
class PlaceResult:
    """Structured place result."""
    place_id: str
    name: str
    address: str
    phone: str = ""
    international_phone: str = ""
    website: str = ""
    types: List[str] = None
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None
    source_query: str = ""
    source_location: str = ""
    
    def __post_init__(self):
        if self.types is None:
            self.types = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'place_id': self.place_id,
            'name': self.name,
            'address': self.address,
            'phone': self.phone,
            'international_phone': self.international_phone,
            'website': self.website,
            'types': self.types,
            'rating': self.rating,
            'user_ratings_total': self.user_ratings_total,
            'source_query': self.source_query,
            'source_location': self.source_location,
        }


class PlacesAcquisition:
    """Google Places API client with caching and rate limiting."""
    
    def __init__(self, config: Config, cache: LeadCache):
        """
        Initialize Places acquisition.
        
        Args:
            config: Application configuration
            cache: Cache instance for storing results
        """
        self.config = config
        self.cache = cache
        
        # Initialize Google Maps client with rate limiting
        self.client = googlemaps.Client(
            key=config.google_api_key,
            queries_per_second=config.queries_per_second,
            retry_over_query_limit=True,
        )
        
        self._api_calls = 0
        self._cache_hits = 0
    
    def search(self, query: str, location: str) -> Generator[PlaceResult, None, None]:
        """
        Search for places matching query near location.
        
        Yields PlaceResult objects as they're fetched.
        Handles pagination automatically.
        
        Args:
            query: Search query (e.g., "plumbers")
            location: Location string (e.g., "Austin, TX")
            
        Yields:
            PlaceResult objects
        """
        logger.info(f"Searching for '{query}' in '{location}'")
        
        # Check for resume progress
        progress = None
        if self.config.resume:
            progress = self.cache.get_search_progress(query, location)
            if progress and progress.get('completed'):
                logger.info(f"Search already completed for '{query}' in '{location}'")
                # Yield cached results
                for place in self.cache.get_places_by_query(query, location):
                    yield self._place_from_cache(place, query, location)
                return
        
        results_fetched = progress.get('results_fetched', 0) if progress else 0
        next_page_token = progress.get('next_page_token') if progress else None
        page = 0 if not next_page_token else (results_fetched // 20)
        
        seen_place_ids = set()
        
        # If resuming, get already-fetched place_ids
        if self.config.resume and results_fetched > 0:
            for place in self.cache.get_places_by_query(query, location):
                seen_place_ids.add(place['place_id'])
                yield self._place_from_cache(place, query, location)
        
        while results_fetched < self.config.max_results and page < self.config.max_pages:
            try:
                # Perform search
                if next_page_token:
                    # Google requires ~2 second delay before using page token
                    time.sleep(2)
                    search_result = self.client.places(query=f"{query} in {location}", page_token=next_page_token)
                else:
                    search_result = self.client.places(query=f"{query} in {location}")
                
                self._api_calls += 1
                
                results = search_result.get('results', [])
                next_page_token = search_result.get('next_page_token')
                
                if not results:
                    logger.info(f"No more results for '{query}' in '{location}'")
                    break
                
                for result in results:
                    place_id = result.get('place_id')
                    if not place_id or place_id in seen_place_ids:
                        continue
                    
                    seen_place_ids.add(place_id)
                    
                    # Fetch details for this place
                    place_result = self._get_place_details(place_id, query, location)
                    if place_result:
                        results_fetched += 1
                        yield place_result
                        
                        if results_fetched >= self.config.max_results:
                            break
                    
                    # Rate limiting sleep
                    time.sleep(self.config.sleep_ms / 1000.0)
                
                # Save progress
                self.cache.save_search_progress(
                    query, location, next_page_token, results_fetched,
                    completed=(not next_page_token or results_fetched >= self.config.max_results)
                )
                
                page += 1
                
                if not next_page_token:
                    break
                    
            except ApiError as e:
                logger.error(f"API error searching '{query}': {e}")
                self.cache.save_failure('search', str(e), place_id=None, domain=None)
                break
            except Timeout:
                logger.error(f"Timeout searching '{query}'")
                self.cache.save_failure('search_timeout', 'Request timed out')
                break
            except TransportError as e:
                logger.error(f"Transport error: {e}")
                self.cache.save_failure('transport', str(e))
                break
        
        # Mark as completed
        self.cache.save_search_progress(query, location, None, results_fetched, completed=True)
        
        logger.info(f"Search complete: {results_fetched} results for '{query}' in '{location}'")
    
    def _get_place_details(self, place_id: str, source_query: str, source_location: str) -> Optional[PlaceResult]:
        """
        Fetch place details, using cache if available.
        
        Args:
            place_id: Google place ID
            source_query: Original search query
            source_location: Original search location
            
        Returns:
            PlaceResult or None if failed
        """
        # Check cache first
        cached = self.cache.get_place(place_id)
        if cached:
            self._cache_hits += 1
            logger.debug(f"Cache hit for place {place_id}")
            return self._place_from_cache(cached, source_query, source_location)
        
        try:
            # Fetch from API with minimal fields
            response = self.client.place(place_id, fields=DETAIL_FIELDS)
            self._api_calls += 1
            
            result = response.get('result', {})
            
            # Save to cache
            self.cache.save_place(
                {'place_id': place_id, 'result': result},
                source_query=source_query,
                source_location=source_location
            )
            
            return PlaceResult(
                place_id=place_id,
                name=result.get('name', ''),
                address=result.get('formatted_address', ''),
                phone=result.get('formatted_phone_number', ''),
                international_phone=result.get('international_phone_number', ''),
                website=result.get('website', ''),
                types=result.get('types', []),
                rating=result.get('rating'),
                user_ratings_total=result.get('user_ratings_total'),
                source_query=source_query,
                source_location=source_location,
            )
            
        except ApiError as e:
            logger.error(f"API error fetching place {place_id}: {e}")
            self.cache.save_failure('place_details', str(e), place_id=place_id)
            return None
        except Exception as e:
            logger.error(f"Error fetching place {place_id}: {e}")
            self.cache.save_failure('place_details', str(e), place_id=place_id)
            return None
    
    def _place_from_cache(self, cached: Dict[str, Any], source_query: str, source_location: str) -> PlaceResult:
        """Convert cached place data to PlaceResult."""
        return PlaceResult(
            place_id=cached.get('place_id', ''),
            name=cached.get('name', ''),
            address=cached.get('address', ''),
            phone=cached.get('phone', ''),
            international_phone=cached.get('international_phone', ''),
            website=cached.get('website', ''),
            types=cached.get('types', []),
            rating=cached.get('rating'),
            user_ratings_total=cached.get('user_ratings_total'),
            source_query=source_query or cached.get('source_query', ''),
            source_location=source_location or cached.get('source_location', ''),
        )
    
    def get_stats(self) -> Dict[str, int]:
        """Get API usage statistics."""
        return {
            'api_calls': self._api_calls,
            'cache_hits': self._cache_hits,
        }


def parse_queries_csv(csv_path: str) -> List[Tuple[str, str]]:
    """
    Parse CSV file of queries and locations.
    
    Expected format:
    query,location
    plumbers,Austin TX
    electricians,Dallas TX
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        List of (query, location) tuples
    """
    import csv
    
    queries = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            query = row.get('query', '').strip()
            location = row.get('location', '').strip()
            if query and location:
                queries.append((query, location))
    
    return queries

